import xmlrpc.server
import threading
import json
import os
import atexit

class LoteGado:
    def __init__(self, id, raca, quantidade, lance_atual, arrematante_atual="Nenhum", status="ABERTO"):
        self.id = id; self.raca = raca; self.quantidade = quantidade; self.lance_atual = float(lance_atual); self.arrematante_atual = arrematante_atual; self.status = status

    def to_dict(self):
        return {
            "id": self.id, "raca": self.raca, "quantidade": self.quantidade,
            "lance_atual": self.lance_atual, "arrematante_atual": self.arrematante_atual, "status": self.status
        }
    
    def __str__(self):
        return (f"ID: {self.id:<2} | Raça: {self.raca:<10} | Qtd: {self.quantidade:<3} | "
                f"Lance Atual: R$ {self.lance_atual:>9.2f} | Arrematante: {self.arrematante_atual:<15} | "
                f"Status: {self.status}")

class LeilaoHandler:
    DATA_FILE = "leilao_data.json"

    def __init__(self):
        self._lotes = []
        self._id_counter = 0
        self._lock = threading.RLock()
        self._clientes_ativos = set() 
        self._carregar_lotes()

    def _salvar_lotes(self):
        with self._lock:
            try:
                with open(self.DATA_FILE, 'w', encoding='utf-8') as f:
                    json.dump([lote.to_dict() for lote in self._lotes], f, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"[SERVIDOR] ERRO ao salvar dados: {e}")

    def _carregar_lotes(self):
        with self._lock:
            if not os.path.exists(self.DATA_FILE): return
            try:
                with open(self.DATA_FILE, 'r', encoding='utf-8') as f:
                    lotes_data = json.load(f)
                    if not lotes_data: return
                    for lote_dict in lotes_data:
                        self._lotes.append(LoteGado(**lote_dict))
                    if self._lotes:
                        self._id_counter = max(lote.id for lote in self._lotes)
                print(f"[SERVIDOR] Dados de leilão carregados.")
            except Exception as e:
                print(f"[SERVIDOR] ERRO ao carregar dados: {e}")

    def conectar_cliente(self, nome_cliente):
        with self._lock:
            if nome_cliente in self._clientes_ativos:
                print(f"[SERVIDOR] Tentativa de conexão recusada. Nome em uso: {nome_cliente}")
                return f"ERRO: O nome '{nome_cliente}' já está em uso. Tente outro."
            self._clientes_ativos.add(nome_cliente)
            print(f"[SERVIDOR] Cliente conectado: {nome_cliente}")
            return "SUCESSO: Conectado ao leilão."

    def desconectar_cliente(self, nome_cliente):
        with self._lock:
            self._clientes_ativos.discard(nome_cliente)
            print(f"[SERVIDOR] Cliente desconectado: {nome_cliente}")
        return "Desconectado com sucesso."
    
    def criar_lote(self, raca, quantidade, preco_inicial):
        with self._lock:
            self._id_counter += 1
            novo_lote = LoteGado(id=self._id_counter, raca=raca, quantidade=int(quantidade), lance_atual=float(preco_inicial))
            self._lotes.append(novo_lote)
        self._salvar_lotes()
        return f"Lote #{self._id_counter} criado."

    def listar_lotes(self):
        with self._lock:
            return [lote.to_dict() for lote in self._lotes]

    def registrar_lance(self, id_lote, valor_lance, nome_arrematante):
        with self._lock:
            try:
                id_lote, valor_lance = int(id_lote), float(valor_lance)
                lote = next((l for l in self._lotes if l.id == id_lote), None)
                if not lote: return "ERRO: Lote não encontrado."
                if lote.status != "ABERTO": return "ERRO: Leilão encerrado."
                if valor_lance <= lote.lance_atual: return f"ERRO: Lance deve ser maior que R${lote.lance_atual:.2f}."
                lote.lance_atual, lote.arrematante_atual = valor_lance, nome_arrematante
                self._salvar_lotes()
                return "SUCESSO: Lance registrado."
            except (ValueError, TypeError) as e:
                return f"ERRO: Dados de entrada inválidos. {e}"

    def encerrar_leilao(self, id_lote):
        with self._lock:
            lote = next((l for l in self._lotes if l.id == int(id_lote)), None)
            if not lote: return "ERRO: Lote não encontrado."
            lote.status = "ENCERRADO"
            self._salvar_lotes()
            return f"Leilão #{lote.id} encerrado. Ganhador: {lote.arrematante_atual}"

    def retirar_lote(self, id_lote):
        with self._lock:
            lote = next((l for l in self._lotes if l.id == int(id_lote)), None)
            if not lote: return "ERRO: Lote não encontrado."
            if lote.arrematante_atual != "Nenhum": return "ERRO: Lote com lances não pode ser retirado."
            self._lotes.remove(lote)
            self._salvar_lotes()
            return f"SUCESSO: Lote #{lote.id} foi retirado."

if __name__ == "__main__":
    HOST, PORT = 'localhost', 8080
    leilao_handler = LeilaoHandler()
    server = xmlrpc.server.SimpleXMLRPCServer((HOST, PORT), allow_none=True)
    server.register_introspection_functions()
    
    server.register_function(leilao_handler.listar_lotes, 'listar_lotes')
    server.register_function(leilao_handler.registrar_lance, 'registrar_lance')
    server.register_function(leilao_handler.conectar_cliente, 'conectar_cliente')
    server.register_function(leilao_handler.desconectar_cliente, 'desconectar_cliente')
    
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print(f"Servidor RPC escutando em http://{HOST}:{PORT} em segundo plano.")
    
    atexit.register(leilao_handler._salvar_lotes)
    print("Console de Administrador iniciado. Digite 'ajuda' para ver os comandos.")
    
    while True:
        try:
            cmd_line = input("> Admin: ")
            parts = cmd_line.split()
            command = parts[0].lower() if parts else ""
            if command == "sair":
                print("Encerrando o servidor...")
                break
            elif command == "listar":
                print("--- Lotes Atuais no Leilão ---")
                for lote in leilao_handler._lotes:
                    print(lote)
                print("------------------------------")
            elif command == "criar" and len(parts) == 4:
                print(leilao_handler.criar_lote(parts[1], parts[2], parts[3]))
            elif command == "retirar" and len(parts) == 2:
                print(leilao_handler.retirar_lote(parts[1]))
            elif command == "encerrar" and len(parts) == 2:
                print(leilao_handler.encerrar_leilao(parts[1]))
            elif command == "ajuda":
                print("\nComandos: listar, criar <raca> <qtd> <preco>, retirar <id>, encerrar <id>, sair\n")
            elif command != "":
                print("Comando desconhecido. Digite 'ajuda'.")
        except Exception as e:
            print(f"Ocorreu um erro: {e}")
            
    server.shutdown()
    print("Servidor encerrado.")