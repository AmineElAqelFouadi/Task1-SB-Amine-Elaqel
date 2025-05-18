# Task1 - SB Amine Elaqel

##Pyro

- **Requisits previs:**
  - `pip install Pyro4`
- **Execució:**
  - `python pyro_insult_filter.py 8001`
  - `python pyro_insult_service.py 9000`
- **Prova normal:**
  - `python pyro_client_demo.py`
- **Anàlisi del rendiment d’un sol node:**
  - `python pyro_StressTest_Combined.py`
- **Anàlisi del rendiment amb múltiples nodes (escalat estàtic):**
  - `python pyro_MultiNodeTest.py`
  - *No cal executar filter ni service; el codi els activa automàticament.*

---

## RabbitMQ

- **Requisits previs:**
  - `pip install pika redis`
- **Execució:**
  - `python InsultProducer_RabbitMQ.py`
  - `python InsultConsumer_RabbitMQ.py`
  - `python InsultService_RabbitMQ.py`
  - `python InsultReceiver_RabbitMQ.py`
  - `python InsultFilter_RabbitMQ.py`
  - `python InsultBroadcaster_RabbitMQ.py` *(opcional)*
- **Prova normal:**
  - `python client_send_texts.py`
- **Anàlisi del rendiment d’un sol node:**
  - `python StressTest_Combined_RabbitMQ.py`
- **Anàlisi del rendiment amb múltiples nodes (escalat estàtic):**
  - `python MultiNodeTest_RabbitMQ.py`
- **Anàlisi del rendiment amb múltiples nodes (escalat dinàmic):**
  - `python autoscaler.py`
  - `python client_send_texts.py`

---

## Redis

- **Requisits previs:**
  - `pip install redis`
- **Execució:**
  - `python insult_service_redis.py`
  - `python insult_filter_redis.py`
- **Prova normal:**
  - `python client_demo_redis.py`
- **Anàlisi del rendiment d’un sol node:**
  - `python StressTest_Combined_redis.py`
- **Anàlisi del rendiment amb múltiples nodes (escalat estàtic):**
  - `python MultiNodeTest_redis.py`
  - *No cal executar filter ni service; el codi els activa automàticament.*

---

## XML-RPC

- **Execució:**
  - `python insult_service.py 8000`
  - `python insult_filter.py 8001`
- **Prova normal:**
  - `python client_demo.py`
- **Anàlisi del rendiment d’un sol node:**
  - `python StressTest_Combined.py`
- **Anàlisi del rendiment amb múltiples nodes (escalat estàtic):**
  - `python MultiNodeTest.py`
  - *No cal executar filter ni service; el codi els activa automàticament.*
