import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import xmlrpc.client

class TelaLeilao:
  
    def __init__(self, master):
    
        self.master = master
        self.master.title("Participante Leilão de Gado")
        self.master.geometry("1280x720") 


        try:
            self.servidor = xmlrpc.client.ServerProxy('http://localhost:8080')
            self.servidor.system.listMethods()
        except Exception as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao servidor.\nVerifique se o servidor está em execução.\n\nErro: {e}")
            self.master.destroy()
            return
        
        self.nome_arrematante = ""
        self.conectado = False

        self.criar_widgets()

        self.conectar_cliente()

        self.master.protocol("WM_DELETE_WINDOW", self.desconectar_cliente)

    def criar_widgets(self):

        
        # Frame para a lista de lotes
        frame_lista = ttk.LabelFrame(self.master, text="Lotes Abertos para Lance")
        frame_lista.pack(pady=10, padx=10, fill="both", expand=True)

        self.lista_lotes = ttk.Treeview(frame_lista, columns=("ID", "Raça", "Qtd", "Lance", "Arrematante"), show="headings")
        self.lista_lotes.heading("ID", text="ID"); self.lista_lotes.column("ID", width=40, anchor="center")
        self.lista_lotes.heading("Raça", text="Raça"); self.lista_lotes.column("Raça", width=150)
        self.lista_lotes.heading("Qtd", text="Qtd"); self.lista_lotes.column("Qtd", width=50, anchor="center")
        self.lista_lotes.heading("Lance", text="Lance Atual"); self.lista_lotes.column("Lance", width=150, anchor="e")
        self.lista_lotes.heading("Arrematante", text="Arrematante Atual"); self.lista_lotes.column("Arrematante", width=200)
        self.lista_lotes.pack(fill="both", expand=True, padx=5, pady=5)

        frame_lance = ttk.LabelFrame(self.master, text="Fazer um Lance")
        frame_lance.pack(pady=10, padx=10, fill="x")

        ttk.Label(frame_lance, text="ID do Lote:").grid(row=0, column=0, padx=5, pady=5)
        self.entry_id = ttk.Entry(frame_lance, width=10)
        self.entry_id.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame_lance, text="Valor do Lance: R$").grid(row=0, column=2, padx=5, pady=5)
        self.entry_valor = ttk.Entry(frame_lance, width=15)
        self.entry_valor.grid(row=0, column=3, padx=5, pady=5)

        self.btn_lance = ttk.Button(frame_lance, text="Dar Lance!", command=self.fazer_lance)
        self.btn_lance.grid(row=0, column=4, padx=10, pady=5)
        

        self.status_label = ttk.Label(self.master, text="Bem-vindo!", relief="sunken", anchor="w")
        self.status_label.pack(side="bottom", fill="x")

    def conectar_cliente(self):

        while not self.conectado:
            nome = simpledialog.askstring("Identificação", "Digite seu nome de arrematante:", parent=self.master)
            if not nome: 
                self.master.destroy()
                return

            try:
                resposta = self.servidor.conectar_cliente(nome)
                if resposta.startswith("SUCESSO"):
                    self.nome_arrematante = nome
                    self.conectado = True
                    self.status_label.config(text=f"Conectado como {self.nome_arrematante}.")
                    self.master.title(f"Leilão de Gado - Cliente (Usuário: {self.nome_arrematante})")

                    self.atualizar_lista_lotes()
                else:
                    messagebox.showerror("Erro de Conexão", resposta)
            except Exception as e:
                messagebox.showerror("Erro Crítico", f"Erro ao conectar: {e}")
                self.master.destroy()
                return

    def desconectar_cliente(self):

        if self.conectado:
            try:
                self.servidor.desconectar_cliente(self.nome_arrematante)
                print("Desconectado do servidor.")
            except Exception as e:
                print(f"Erro ao tentar desconectar: {e}")
        self.master.destroy()

    def fazer_lance(self):

        id_lote = self.entry_id.get()
        valor_lance = self.entry_valor.get()
        
        if not id_lote or not valor_lance:
            self.status_label.config(text="ERRO: Preencha o ID do lote e o valor do lance.")
            return

        try:
            resultado = self.servidor.registrar_lance(id_lote, valor_lance, self.nome_arrematante)
            self.status_label.config(text=f"SERVIDOR: {resultado}")
            if resultado.startswith("SUCESSO"):

                self.entry_id.delete(0, 'end')
                self.entry_valor.delete(0, 'end')

                self.atualizar_lista_lotes()
        except Exception as e:
            self.status_label.config(text=f"ERRO DE COMUNICAÇÃO: {e}")

    def atualizar_lista_lotes(self):

        if not self.conectado: return

        try:
 
            for item in self.lista_lotes.get_children():
                self.lista_lotes.delete(item)
            
            lotes = self.servidor.listar_lotes()
            for lote in lotes:
                if lote['status'] == "ABERTO":
                    lance_formatado = f"R$ {lote['lance_atual']:.2f}"
                    self.lista_lotes.insert("", "end", values=(
                        lote['id'], lote['raca'], lote['quantidade'], 
                        lance_formatado, lote['arrematante_atual']
                    ))
        except Exception as e:
            self.status_label.config(text=f"Erro ao atualizar lista: {e}")

        self.master.after(5000, self.atualizar_lista_lotes)

if __name__ == "__main__":
    root = tk.Tk()
    app = TelaLeilao(root)
    root.mainloop()