import customtkinter as ctk
import os
import sys
import darkdetect

# Nome do arquivo de configuração
NOME_ARQUIVO_CONFIG = "config_pista_2N_Aruja.txt"  # Você pode mudar isso, ex: "configuracoes_12N_Itatiaia.txt"


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
        self.title("Configurador de Parâmetros da Câmera")
        self.geometry("700x850")  # Aumentei um pouco a altura para acomodar tudo
        ctk.set_appearance_mode("Dark")
        self.configure(fg_color=self.COLOR_WINDOW_BG)

        self.widgets = {}

        self.create_widgets()
        self.load_config()

    def create_widgets(self):
        scrollable_frame = ctk.CTkScrollableFrame(
            self,
            label_text="Configurações da Pista",
            label_font=ctk.CTkFont(size=20, weight="bold"),
            label_text_color=self.COLOR_HEADER,
            fg_color=self.COLOR_FRAME_BG,
            scrollbar_button_color=self.COLOR_ENTRY_BORDER
        )
        scrollable_frame.pack(pady=10, padx=20, fill="both", expand=True)

        # --- Seções de Configuração COMPLETAS ---
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
        self.create_entry(scrollable_frame, "PERFIL_NORMAL_SHUTTER", "Normal - Shutter:")
        self.create_entry(scrollable_frame, "PERFIL_NORMAL_GAMMA", "Normal - Gamma:")
        self.create_entry(scrollable_frame, "PERFIL_SOL_MEDIO_SHUTTER", "Sol Médio - Shutter:")
        self.create_entry(scrollable_frame, "PERFIL_SOL_MEDIO_GAMMA", "Sol Médio - Gamma:")
        self.create_entry(scrollable_frame, "PERFIL_SOL_FORTE_SHUTTER", "Sol Forte - Shutter:")
        self.create_entry(scrollable_frame, "PERFIL_SOL_FORTE_GAMMA", "Sol Forte - Gamma:")

        self.create_section_header(scrollable_frame, "Limiares para Ativar Modo Anti-Sol")
        self.create_entry(scrollable_frame, "CONTADOR_PARA_ESCALAR", "Contador para Ativar:")
        self.create_entry(scrollable_frame, "LIMIAR_ESTOURO_ALERTA_INICIAL", "Estouro para Alerta Inicial (%):")
        self.create_entry(scrollable_frame, "LIMIAR_BRILHO_MEDIO_SOL_MEDIO", "Brilho p/ Sol Médio (>):")
        self.create_entry(scrollable_frame, "LIMIAR_GANHO_SOL_MEDIO", "Ganho p/ Sol Médio (<):")
        self.create_entry(scrollable_frame, "LIMIAR_BRILHO_MEDIO_SOL_FORTE", "Brilho p/ Sol Forte (>):")
        self.create_entry(scrollable_frame, "LIMIAR_GANHO_SOL_FORTE", "Ganho p/ Sol Forte (<):")
        self.create_entry(scrollable_frame, "LIMIAR_ESTOURO_ESCALADA_MEDIA", "Estouro p/ Escalar de Médio->Forte (%):")

        self.create_section_header(scrollable_frame, "Limiares para Voltar ao Modo Normal")
        self.create_entry(scrollable_frame, "CONTADOR_PARA_DESESCALAR", "Contador para Desativar:")
        self.create_entry(scrollable_frame, "LIMIAR_ESTOURO_OK", "Estouro OK (< %):")
        self.create_entry(scrollable_frame, "LIMIAR_BRILHO_MEDIO_PARA_NORMAL", "Brilho p/ Voltar ao Normal (<):")
        self.create_entry(scrollable_frame, "LIMIAR_BRILHO_MEDIO_PARA_MEDIO", "Brilho p/ Voltar de Forte->Médio (<):")

        self.create_section_header(scrollable_frame, "Parâmetros de Análise")
        self.create_entry(scrollable_frame, "NOME_PARAM_GANHO_ATUAL", "Nome do Parâmetro de Ganho:")
        self.create_entry(scrollable_frame, "LIMIAR_BRILHO_PIXEL_ESTOURADO", "Brilho do Pixel Estourado (0-255):")

        self.create_section_header(scrollable_frame, "Debug e Salvamento de Imagens")
        self.create_entry(scrollable_frame, "DIRETORIO_IMAGENS_ALERTA", "Pasta para Imagens de Alerta:")
        self.create_entry(scrollable_frame, "DIRETORIO_IMAGENS_CROPADAS", "Pasta para Imagens de Debug (Crop):")
        self.create_checkbox(scrollable_frame, "SALVAR_IMAGEM_NO_ALERTA", "Salvar Imagens de Alerta")
        self.create_checkbox(scrollable_frame, "SALVAR_IMAGEM_CROPADA_DEBUG", "Salvar Imagens de Debug (Crop)")

        # --- Botões de Ação ---
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(pady=10, fill="x")

        save_button = ctk.CTkButton(
            button_frame,
            text="Salvar Configurações",
            command=self.save_config,
            fg_color=self.COLOR_BUTTON_SAVE,
            hover_color="#2EA043"
        )
        save_button.pack(side="left", padx=20)

        exit_button = ctk.CTkButton(
            button_frame,
            text="Sair",
            command=self.destroy,
            fg_color=self.COLOR_BUTTON_EXIT,
            hover_color="#39414A"
        )
        exit_button.pack(side="right", padx=20)

        self.status_label = ctk.CTkLabel(self, text="", text_color=self.COLOR_TEXT, font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=(0, 10), fill="x")

    def create_section_header(self, parent, text):
        header = ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=14, weight="bold", underline=True),
                              text_color=self.COLOR_HEADER)
        header.pack(pady=(15, 5), padx=10, anchor="w")

    def create_entry(self, parent, key, label_text):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=10, pady=3)
        label = ctk.CTkLabel(frame, text=label_text, width=280, anchor="w", text_color=self.COLOR_TEXT)
        label.pack(side="left")
        entry = ctk.CTkEntry(
            frame,
            fg_color=self.COLOR_ENTRY_BG,
            border_color=self.COLOR_ENTRY_BORDER,
            text_color=self.COLOR_TEXT
        )
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
                        widget.delete(0, "end");
                        widget.insert(0, value)
                    elif isinstance(widget, ctk.CTkCheckBox):
                        if value.lower() == 'true':
                            widget.select()
                        else:
                            widget.deselect()
            self.status_label.configure(text="Configurações carregadas com sucesso.", text_color="green")
        except FileNotFoundError:
            self.status_label.configure(
                text=f"'{NOME_ARQUIVO_CONFIG}' não encontrado. Preencha e salve para criar um novo.",
                text_color="orange")
        except Exception as e:
            self.status_label.configure(text=f"Erro ao carregar: {e}", text_color="red")

    def save_config(self):
        config_path = self.get_config_path()
        try:
            # Lista completa de chaves na ordem desejada para salvar o arquivo
            all_keys = [
                "NOME_PISTA", "CAMERA_IP", "CLP_IP", "HORA_ENCERRAMENTO",
                "CROP_X1", "CROP_Y1", "CROP_X2", "CROP_Y2",
                "PERFIL_NORMAL_SHUTTER", "PERFIL_NORMAL_GAMMA",
                "PERFIL_SOL_MEDIO_SHUTTER", "PERFIL_SOL_MEDIO_GAMMA",
                "PERFIL_SOL_FORTE_SHUTTER", "PERFIL_SOL_FORTE_GAMMA",
                "CONTADOR_PARA_ESCALAR", "LIMIAR_ESTOURO_ALERTA_INICIAL",
                "LIMIAR_BRILHO_MEDIO_SOL_MEDIO", "LIMIAR_GANHO_SOL_MEDIO",
                "LIMIAR_BRILHO_MEDIO_SOL_FORTE", "LIMIAR_GANHO_SOL_FORTE",
                "LIMIAR_ESTOURO_ESCALADA_MEDIA", "CONTADOR_PARA_DESESCALAR",
                "LIMIAR_ESTOURO_OK", "LIMIAR_BRILHO_MEDIO_PARA_NORMAL",
                "LIMIAR_BRILHO_MEDIO_PARA_MEDIO", "NOME_PARAM_GANHO_ATUAL",
                "LIMIAR_BRILHO_PIXEL_ESTOURADO", "DIRETORIO_IMAGENS_ALERTA",
                "DIRETORIO_IMAGENS_CROPADAS", "SALVAR_IMAGEM_NO_ALERTA",
                "SALVAR_IMAGEM_CROPADA_DEBUG"
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