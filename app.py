from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from datetime import date, datetime
import uvicorn, asyncio, requests

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STREAM_DELAY = 1
RETRY_TIMEOUT = 1000

clientes = [
]

class Compromisso(BaseModel):
    nome_evento: str
    data: str
    alerta: int
    alertado: int

class Cliente(BaseModel):
    nome: str = ''
    compromissos: list = []

@app.post('/cadastro_cliente')
def cadastro_cliente(nome: str):
    clientes.append(Cliente(nome=nome))

    return {"cliente adicionado": clientes[-1]}

@app.post('/{nome}/cadastro_compromisso')
def cadastro_compromisso(nome: str, comp: Compromisso):
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
            if c.nome == nome:
                for comp in c.compromissos:
                    if comp.alertado == 0:
                        now = datetime.now().timestamp()
                        horario = datetime.strptime(comp.data, "%d/%m/%Y %H:%M").timestamp()
                        if (horario - now)/ 60 <= comp.alerta:
                            comp.alertado = 1
                            return comp, True
        return None, False
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break

            # Checks for new messages and return them to client if any
            c, new = new_messages()
            if new:
                yield {
                        "event": "new_message",
                        "id": "message_id",
                        "retry": RETRY_TIMEOUT,
                        "data": f"Voce tem um compromisso daqui {c.alerta} minutos"
                }

            await asyncio.sleep(STREAM_DELAY)

    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    base_url = 'http://localhost:8000'
    params = {'nome':'Lucas'}
    cadastro_c = '/cadastro_cliente'
    print(requests.post(base_url+cadastro_c, params=params).text)

    cadastro_comp = f'/{params["nome"]}/cadastro_compromisso'
    data = '{"nome_evento":"Teste", "data":"28/11/2022 21:50", "alerta":5, "alertado":0}'
    print(requests.post(base_url+cadastro_comp, data=data).text)

