# Task1 SB Amine Elaqel
 Pyro:
Requisits previs: pip install Pyro4
Execució: python pyro_insult_filter.py 8001
python pyro_insult_service.py 9000
Si vols fer una prova normal -> python pyro_client_demo.py
Análisis del rendimiento de un solo nodo -> python pyro_StressTest_Combined.py
Análisis del rendimiento del escalamiento estático de múltiples nodos -> python pyro_MultiNodeTest.py
(Per a realitzar aquest test no cal executar el filter ni el service, ja que en el propi codi els active)

Rabbit:
Requisits previs: pip install pika redis
Execució: python InsultProducer_RabbitMQ.py
python InsultConsumer_RabbitMQ.py
python InsultService_RabbitMQ.py
python InsultReceiver_RabbitMQ.py
python InsultFilter_RabbitMQ.py
python InsultBroadcaster_RabbitMQ.py   (Opciona)
Si vols fer una prova normal ->python client_send_texts.py
Análisis del rendimiento de un solo nodo -> python StressTest_Combined_RabbitMQ.py
Análisis del rendimiento del escalamiento estático de múltiples nodos -> python MultiNodeTest_RabbitMQ.py
Anàlisi del rendiment de l'escala dinàmica de diversos nodes  -> python autoscaler.py   i tambe python client_send_texts.py

Redis:
Requisits previs: pip install redis
Execució: python insult_service_redis.py
python insult_filter_redis.py
Si vols fer una prova normal -> python client_demo_redis.py
Análisis del rendimiento de un solo nodo -> python StressTest_Combined_redis.py
Análisis del rendimiento del escalamiento estático de múltiples nodos -> python MultiNodeTest_redis.py
(Per a realitzar aquest test no cal executar el filter ni el service, ja que en el propi codi els active)

XMLRPC:
Execució: python insult_service.py 8000
python insult_filter.py 8001
Si vols fer una prova normal -> python client_demo.py
Análisis del rendimiento de un solo nodo -> python StressTest_Combined.py
Análisis del rendimiento del escalamiento estático de múltiples nodos -> python MultiNodeTest.py
(Per a realitzar aquest test no cal executar el filter ni el service, ja que en el propi codi els active)

 
