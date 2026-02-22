import customtkinter as ctk
import os
import sys

# Nome do arquivo de configuração (igual ao do script principal)
NOME_ARQUIVO_CONFIG = "config_pista_img_escura_19S.txt"

class ConfigApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Paleta de Cores (Tema "Dark Tech") ---
        self.COLOR_WINDOW_BG = "#0D1117"
        self.COLOR_FRAME_BG = "#161B22"
        self.COLOR_TEXT = "#FFFFFF"
        self.COLOR_HEADER = "#58A6FF"
        self.COLOR_ENTRY_BG = "#21262D"
        self.COLOR_ENTRY_BORDER = "#30363D"
        self.COLOR_BUTTON_SAVE = "#238636"
        self.COLOR_BUTTON_EXIT = "#30363D"

        # --- Configurações da Janela ---
        self.title("Configurador de Câmera - Modo Imagem Escura")
        self.geometry("700x650")
        ctk.set_appearance_mode("Dark")
        self.configure(fg_color=self.COLOR_WINDOW_BG)

        self.widgets = {}
        self.create_widgets()
        self.load_config()

    def create_widgets(self):
        scrollable_frame = ctk.CTkScrollableFrame(
            self,
            label_text="Configurações da Pista (Imagem Escura)",
            label_font=ctk.CTkFont(size=20, weight="bold"),
            label_text_color=self.COLOR_HEADER,
            fg_color=self.COLOR_FRAME_BG,
            scrollbar_button_color=self.COLOR_ENTRY_BORDER
        )
        scrollable_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # --- Seções de Configuração Adaptadas ---
        self.create_section_header(scrollable_frame, "Identificação e Rede")
        self.create_entry(scrollable_frame, "NOME_PISTA", "Nome da Pista:")
        self.create_entry(scrollable_frame, "CAMERA_IP", "IP da Câmera:")
        self.create_entry(scrollable_frame, "CLP_IP", "IP do CLP:")
        self.create_entry(scrollable_frame, "HORA_ENCERRAMENTO", "Hora de Encerramento (HH:MM):")

        self.create_section_header(scrollable_frame, "Região de Interesse (ROI)")
        self.create_entry(scrollable_frame, "CROP_X1", "Corte - X inicial (esquerda):")
        self.create_entry(scrollable_frame, "CROP_Y1", "Corte - Y inicial (topo):")
        self.create_entry(scrollable_frame, "CROP_X2", "Corte - X final (direita):")
        self.create_entry(scrollable_frame, "CROP_Y2", "Corte - Y final (base):")

        self.create_section_header(scrollable_frame, "Perfis de Câmera")
        self.create_entry(scrollable_frame, "PERFIL_NORMAL_SATURACAO", "Normal - Saturação:")
        self.create_entry(scrollable_frame, "PERFIL_NORMAL_GAMMA", "Normal - Gamma:")
        self.create_entry(scrollable_frame, "PERFIL_BAIXA_LUZ_SATURACAO", "Baixa Luz - Saturação:")
        self.create_entry(scrollable_frame, "PERFIL_BAIXA_LUZ_GAMMA", "Baixa Luz - Gamma:")
        self.create_entry(scrollable_frame, "PERFIL_NORMAL_SATURACAODIURNO", "Normal - SaturacaoDiurna:")
        self.create_entry(scrollable_frame, "PERFIL_BAIXA_LUZ_SATURACAODIURNO", "Baixa Luz - SaturacaoDiurna:")

        self.create_section_header(scrollable_frame, "Limiares de Decisão (Histerese)")
        self.create_entry(scrollable_frame, "LIMIAR_BRILHO_ESCURECEU", "Brilho para ATIVAR correção (<):")
        self.create_entry(scrollable_frame, "LIMIAR_BRILHO_CLAREOU", "Brilho para DESATIVAR correção (>):")

        self.create_section_header(scrollable_frame, "Debug e Salvamento de Imagens")
        self.create_entry(scrollable_frame, "DIRETORIO_IMAGENS_ALERTA", "Pasta para Imagens de Alerta:")
        self.create_entry(scrollable_frame, "DIRETORIO_IMAGENS_CROPADAS", "Pasta para Imagens de Debug (Crop):")
        self.create_checkbox(scrollable_frame, "SALVAR_IMAGEM_NO_ALERTA", "Salvar Imagens de Alerta (Escuras)")
        self.create_checkbox(scrollable_frame, "SALVAR_IMAGEM_CROPADA_DEBUG", "Salvar Imagens de Debug (Crop)")

        # --- Botões de Ação ---
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=10, fill="x")
        save_button = ctk.CTkButton(
            button_frame, text="Salvar Configurações",
            command=self.save_config, fg_color=self.COLOR_BUTTON_SAVE, hover_color="#2EA043"
        )
        save_button.pack(side="left", padx=20)
        exit_button = ctk.CTkButton(
            button_frame, text="Sair",
            command=self.destroy, fg_color=self.COLOR_BUTTON_EXIT, hover_color="#39414A"
        )
        exit_button.pack(side="right", padx=20)

        self.status_label = ctk.CTkLabel(self, text="", text_color=self.COLOR_TEXT, font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=(0, 10), fill="x")

    def create_section_header(self, parent, text):
        header = ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=14, weight="bold", underline=True), text_color=self.COLOR_HEADER)
        header.pack(pady=(15, 5), padx=10, anchor="w")

    def create_entry(self, parent, key, label_text):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=3)
        label = ctk.CTkLabel(frame, text=label_text, width=280, anchor="w", text_color=self.COLOR_TEXT)
        label.pack(side="left")
        entry = ctk.CTkEntry(frame, fg_color=self.COLOR_ENTRY_BG, border_color=self.COLOR_ENTRY_BORDER, text_color=self.COLOR_TEXT)
        entry.pack(side="left", fill="x", expand=True)
        self.widgets[key] = entry

    def create_checkbox(self, parent, key, text):
        checkbox = ctk.CTkCheckBox(parent, text=text, text_color=self.COLOR_TEXT)
        checkbox.pack(pady=5, padx=10, anchor="w")
        self.widgets[key] = checkbox

    def get_config_path(self):
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, NOME_ARQUIVO_CONFIG)

    def load_config(self):
        config_path = self.get_config_path()
        try:
            config_data = {}
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.split('=', 1)
                        config_data[key.strip()] = value.strip()

            for key, widget in self.widgets.items():
                if key in config_data:
                    value = config_data[key]
                    if isinstance(widget, ctk.CTkEntry):
                        widget.delete(0, "end")
                        widget.insert(0, value)
                    elif isinstance(widget, ctk.CTkCheckBox):
                        if value.strip().lower() == 'true':
                            widget.select()
                        else:
                            widget.deselect()

            self.status_label.configure(text="Configurações carregadas com sucesso.", text_color="green")

        except FileNotFoundError:
            self.status_label.configure(
                text=f"'{NOME_ARQUIVO_CONFIG}' não encontrado. Preencha e salve para criar um novo.",
                text_color="orange"
            )
        except Exception as e:
            self.status_label.configure(text=f"Erro ao carregar: {e}", text_color="red")

    def save_config(self):
        config_path = self.get_config_path()
        try:
            # Lista de chaves para o arquivo de imagem escura
            all_keys = [
                "NOME_PISTA", "CAMERA_IP", "CLP_IP", "HORA_ENCERRAMENTO",
                "CROP_X1", "CROP_Y1", "CROP_X2", "CROP_Y2",
                "PERFIL_NORMAL_SATURACAO", "PERFIL_NORMAL_GAMMA",
                "PERFIL_BAIXA_LUZ_SATURACAO", "PERFIL_BAIXA_LUZ_GAMMA",
                "PERFIL_NORMAL_SATURACAODIURNO", "PERFIL_BAIXA_LUZ_SATURACAODIURNO",
                "LIMIAR_BRILHO_ESCURECEU", "LIMIAR_BRILHO_CLAREOU",
                "DIRETORIO_IMAGENS_ALERTA", "DIRETORIO_IMAGENS_CROPADAS",
                "SALVAR_IMAGEM_NO_ALERTA", "SALVAR_IMAGEM_CROPADA_DEBUG"
            ]
            with open(config_path, 'w', encoding='utf-8') as f:
                for key in all_keys:
                    if key in self.widgets:
                        widget = self.widgets[key]
                        if isinstance(widget, ctk.CTkEntry):
                            value = widget.get()
                        elif isinstance(widget, ctk.CTkCheckBox):
                            value = "True" if widget.get() == 1 else "False"
                        f.write(f"{key} = {value}\n")

            self.status_label.configure(text="Configurações salvas com sucesso!", text_color="green")

        except Exception as e:
            self.status_label.configure(text=f"Erro ao salvar: {e}", text_color="red")


if __name__ == "__main__":
    app = ConfigApp()
    app.mainloop()
