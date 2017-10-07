Application-Server
======================

  - [Introducción](#introducción)
  - [Tecnologias utilizadas](#tecnologias-utilizadas)
  - [¿Como levantar el servidor?](#como-levantar-el-servidor)

## Introducción ##

Se trata de una aplicación por consola destinada a mantenerse en ejecución por períodos prolongados de tiempo.
Esta aplicación debe brinda una interfaz REST para la comunicación de los diferentes clientes (choferes y pasajeros) que se conecten. El objetivo principal de cara a los choferes es proveerles los posibles viajes a realizar, y de cara a los pasajeros es mostrarles los posibles choferes para que realicen el viaje.
Este servidor se comunicará con el Shared server (explicado a continuación) a través de la interfaz REST común definida para el mismo. En el caso que la aplicación Android necesitara de algún servicio del Shared Server, el Application server actuará de fachada.


## Tecnologias utilizadas ##

Las tecnologías utilizadas para el primer checkpoint fueron:
- Flask 0.12.2
- Python 2.7.10
- Gunicorn 19.7.1
- Travis (para la integración continua)
- Codecov (para coverage de testing)


## Como levantar el servidor ##

Para levantar el servidor es necesario correr los siguientes comandos: 

    git clone https://github.com/Taller2Uber/application-server.git

    cd application-server
   
    sudo apt-get install python-pip
    
    pip install -r requirements.txt
    
Con todo instalado, procedemos a levantar el servidor:

    source llevame/bin/activate

    gunicorn llevame:app
    
El servidor ahora se encontrará levantado en [localhost:8000].

Si el puerto 8000 se encontrara ocupado por otro proceso, se deberá correr el siguiente comando para especificar en que puerto queremos levantarlo.

    gurnicorn --bind 0.0.0.0:XXXX llevame:app
