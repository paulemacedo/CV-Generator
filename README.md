# CV Generator
Este projeto é um gerador de currículos que utiliza templates HTML e CSS para criar currículos personalizados em diferentes idiomas e estilos. Os currículos são exportados em HTML e PDF.

## Pré-requisitos
Certifique-se de ter o seguinte instalado em sua máquina:
- Python 3.9 ou superior
- Gerenciador de pacotes `pip`

## Instalação
1. Clone este repositório para sua máquina local:
   ```bash
   git clone https://github.com/paulemacedo/CV-Generator.git
   ```
2. Navegue até o diretório do projeto:
   ```bash
   cd CV-Generator
   ```
3. Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   ```
   No Windows:
   ```bash
   .venv\Scripts\activate
   ```
   Em Linux/macOS:
   ```bash
   source .venv/bin/activate
   ```
4. Instale as dependências necessárias dentro do ambiente virtual:
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```
5. Instale o Chromium para geração de PDFs:
   ```bash
   python -m playwright install chromium
   ```

## Estrutura do Projeto
- `generate.py`: Script principal para gerar os currículos.
- `data/`: Contém os arquivos JSON com os dados de entrada para os currículos.
- `output/`: Diretório onde os currículos gerados serão salvos.
- `templates/`: Contém os templates HTML e CSS para os currículos.

## Como Usar
1. Prepare os dados de entrada:
   - Copie `data/example.json` para um novo arquivo em `data/` e ajuste as informações necessárias para o currículo.
2. Execute o script para gerar todos os currículos:
   ```bash
   python generate.py
   ```
   - O script detecta automaticamente os idiomas disponíveis (`pt`/`en`) em cada arquivo JSON e gera somente esses idiomas por perfil.
   - JSONs híbridos (parte bilíngue + parte monolíngue) continuam funcionando: campos sem tradução explícita são reaproveitados no idioma em geração.
   - JSONs monolíngues também são suportados.
3. Opcionalmente, solicite idioma/template pela linha de comando:
   ```bash
   python generate.py en
   python generate.py pt ivory
   python generate.py all all
   ```
   - Se um idioma for solicitado mas não existir naquele perfil, o script avisa e ignora esse idioma apenas para o perfil afetado.
4. Os currículos gerados serão salvos no diretório `output/` com padrão pronto para envio:
   - PDFs finais: `output/`
   - HTMLs auxiliares (debug/ajuste visual): `output/html/`

   Padrão de nome dos arquivos:
   - `CV-Nome-Area-Idioma`
   - Exemplo: `CV-Paule-Macedo-Security-PT-BR.pdf`

   Estrutura atual:
   ```
   output/
   ├── CV-Paule-Macedo-Security-PT-BR.pdf
   ├── CV-Paule-Macedo-Security-EN-US.pdf
   └── html/
      ├── CV-Paule-Macedo-Security-PT-BR.html
      └── CV-Paule-Macedo-Security-EN-US.html
   ```

## Personalização
1. **Templates HTML e CSS**:
   - Edite os arquivos em `templates/` para personalizar o estilo e o layout dos currículos.
2. **Dados de Entrada**:
   - Adicione ou modifique os arquivos JSON em `data/` para incluir novas informações.

## Contribuição
Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Licença
Este projeto está licenciado sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.