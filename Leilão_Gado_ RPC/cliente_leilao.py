import xmlrpc.client
import time
import os

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def formatar_lote(lote):
    if lote['status'] != "ABERTO":
        return None
    return (f"ID: {lote['id']:<2} | Raça: {lote['raca']:<10} | Qtd: {lote['quantidade']:<3} | "
            f"Lance Atual: R$ {lote['lance_atual']:>9.2f} | "
            f"Arrematante Atual: {lote['arrematante_atual']:<15}")

def exibir_menu_cliente():
    print("\nComandos disponíveis:")
    print("  lance <id> <valor>  - Para fazer um lance.")
    print("  sair                - Para encerrar o cliente.")
    print("  (Pressione Enter para atualizar a lista de lotes)\n")

if __name__ == "__main__":
    SERVER_URL = 'http://localhost:8080'
    try:
        servidor = xmlrpc.client.ServerProxy(SERVER_URL)
        servidor.system.listMethods()
    except Exception as e:
        print(f"Erro ao conectar ao servidor: {e}")
        exit()

    nome_arrematante = input("Digite seu nome de arrematante: ")
    
    try:
        resposta_conexao = servidor.conectar_cliente(nome_arrematante)
        if resposta_conexao.startswith("ERRO"):
            print(resposta_conexao)
            exit()
        
        print(resposta_conexao)
        time.sleep(2)
        
        while True:
            limpar_tela()
            print(f"--- Leilão de Gado (Arrematante: {nome_arrematante}) ---")
            print("--- LOTES ABERTOS PARA LANCE ---")
            
            lotes = servidor.listar_lotes()
            lotes_abertos = 0
            for lote_data in lotes:
                lote_formatado = formatar_lote(lote_data)
                if lote_formatado:
                    print(lote_formatado)
                    lotes_abertos += 1
            
            if lotes_abertos == 0:
                print("\nNenhum lote aberto para lances no momento.")
            
            print("-" * 70)
            exibir_menu_cliente()
            
            entrada = input(f"> {nome_arrematante}: ")
            partes = entrada.split()
            comando = partes[0].lower() if partes else ""

            if comando == "sair":
                break
            elif comando == "lance" and len(partes) == 3:
                resultado = servidor.registrar_lance(partes[1], partes[2], nome_arrematante)
                print(f"\n[RESPOSTA DO SERVIDOR] -> {resultado}")
                time.sleep(2)
            elif comando != "":
                print("\nComando inválido. Tente novamente.")
                time.sleep(2)

    except KeyboardInterrupt:
        print("\nSaindo...")
    except Exception as e:
        print(f"\nErro de comunicação com o servidor: {e}")
    finally:
        print("Desconectando do servidor...")
        servidor.desconectar_cliente(nome_arrematante)

    print("\nObrigado por participar do leilão!")