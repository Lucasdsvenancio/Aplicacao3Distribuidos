from fastapi import FastAPI, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from datetime import date, datetime
import asyncio

app = FastAPI()

STREAM_DELAY = 1
RETRY_TIMEOUT = 15000

clientes = [
]

class Compromisso(BaseModel):
    nome_evento: str
    data: str
    alerta: int
    alertado: bool

class Cliente(BaseModel):
    nome: str = ''
    compromissos: list = []

@app.post('/cadastro_cliente')
def cadastro_cliente(cliente: Cliente):
    clientes.append(cliente)
    return {"cliente adicionado": clientes[-1]}

@app.post('/{nome}/cadastro_compromisso')
def cadastrar_compromisso(nome: str, comp: Compromisso):
    for c in clientes:
        if c.nome == nome:
            c.compromissos.append(comp)
            return {"compromisso adicionado": c.compromissos[-1]}
    return {'cliente não encontrado'}

@app.post("/{nome}/{nome_evento}/cancelar_compromisso")
def cancelar_compromisso(nome: str, nome_evento: str):
    for c in clientes:
        if c.nome == nome:
            comp = [cm for cm in c.compromissos if cm.nome_evento == nome_evento]
            for cm in comp:
                c.compromissos.remove(cm)
                return {"compromisso excluido"}
            return {"nenhum compromisso encontrado"}
    return {"nenhum cliente encontrado"}
                    
@app.post("/{nome}/{nome_evento}/cancelar_alerta")
def cancelar_alerta(nome: str, nome_evento: str):
    for c in clientes:
        if c.nome == nome:
            for cm in c.compromissos:
                if cm.nome_evento == nome_evento:
                    cm.alerta = 0
                    return {f"compromisso {cm.nome_evento} teve seu alerta cancelado"}
            return {"nenhum compromisso encontrado"}
    return {"nenhum cliente encontrado"}

@app.get("/{nome}/consultar_compromissos")
def consultar_compromisso(nome : str):
    for c in clientes:
        if c.nome == nome:
            return {f"lista de compromissos de {nome}": c.compromissos}
            
        
@app.get("/{nome}/stream")
async def message_stream(nome: str, request: Request):
    def new_messages():
        for c in clientes:
            if c.nome == nome and c.alertado == 0:
                now = datetime.now().timestamp()
                horario = datetime.strptime(c.data, "%d/%m/%Y %H:%M").timestamp()
                if (horario - now)/ 60 <= c.alerta:
                    yield "Voce tem um compromisso daqui {c.alerta} minutos"
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break

            # Checks for new messages and return them to client if any
            if new_messages():
                yield {
                        "event": "new_message",
                        "id": "message_id",
                        "retry": RETRY_TIMEOUT,
                        "data": "message_content"
                }

            await asyncio.sleep(STREAM_DELAY)

    return EventSourceResponse(event_generator())