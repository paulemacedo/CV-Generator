# CV Generator

Este projeto é um gerador de currículos que utiliza templates HTML e CSS para criar currículos personalizados em diferentes idiomas e estilos.

## Pré-requisitos

Certifique-se de ter o seguinte instalado em sua máquina:

- Python 3.8 ou superior
- Gerenciador de pacotes `pip`

## Instalação

1. Clone este repositório para sua máquina local:
   ```bash
   git clone <URL_DO_REPOSITORIO>
   ```

2. Navegue até o diretório do projeto:
   ```bash
   cd CV-Generator
   ```

3. Instale as dependências necessárias:
   ```bash
   pip install -r requirements.txt
   ```

## Estrutura do Projeto

- `generate.py`: Script principal para gerar os currículos.
- `data/`: Contém os arquivos JSON com os dados de entrada para os currículos.
- `output/`: Diretório onde os currículos gerados serão salvos.
- `templates/`: Contém os templates HTML e CSS para os currículos.

## Como Usar

1. Prepare os dados de entrada:
   - Edite ou crie um arquivo JSON no diretório `data/` com as informações necessárias para o currículo. Veja o exemplo em `data/example.json`.

2. Execute o script para gerar todos os currículos:
   ```bash
   python generate.py
   ```
   - O script agora gera automaticamente todos os currículos para todos os idiomas e templates disponíveis.

3. Os currículos gerados serão salvos no diretório `output/`.

## Personalização

1. **Templates HTML e CSS**:
   - Edite os arquivos em `templates/` para personalizar o estilo e o layout dos currículos.

2. **Dados de Entrada**:
   - Adicione ou modifique os arquivos JSON em `data/` para incluir novas informações.

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
