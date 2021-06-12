## README para auxiliar ambiente de desenvolvimento

### Pré-requisitos
<!--ts-->
  * Ter python3 instalado na máquina
<!--te-->

### Clonando o repositório:
<!--ts-->
  * Clonar repositório do github para máquina local
  * Criar virtual env (passos no Windows (prompt) abaixo)
    * python -m venv C:\path-até-root-desse projeto/venv
    * Mais info em "https://docs.python.org/3/library/venv.html"
  * Ativar venv
    * C:\path-até-root-desse-projeto\venv\Scripts\activate
  * Instalar bibliotecas do projeto dentro do venv
    * Na pasta root do projeto, rodar "pip install -r requirements.txt"
<!--te-->

### Modificar informações conexão serial
<!--ts-->
  * Modificar os campos no arquivo serial_config.ini
    * port -> porta que o esp está conectado
    * baudrate -> bit rate da conexão serial
<!--te-->