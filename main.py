from fastapi import FastAPI, WebSocket, WebSocketDisconnect , Request
from fastapi.responses import FileResponse

import openai
import time
import os



app = FastAPI()


os.environ["OPENAI_API_KEY"] = "Your_openai_key" #OPENAI_API_KEY

client = openai.OpenAI()

# record the time before the request is sent
start_time = time.time()


def call_open_api(message):
    completion = client.chat.completions.create(
        model='gpt-3.5-turbo',
        
        messages=[
            {"role": "system", "content": "You are a assistance named Bluu , A asistance from scalebuildAI , you help people to find the best product for them , Scalebuild ios a software company"},
            #add 10 last messages history here

            {'role': 'user', 'content': message}
        ],
        temperature=0,
        stream=True  # again, we set stream=True
    )

    return completion
    # create variables to collect the stream of chunks
    
    
    

class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_text(self, text: str, websocket: WebSocket):
        await websocket.send_text(text)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            try:
                # Receive text data (speech recognition result) from the client
                data = await websocket.receive_text()
                
                # Process the data
                print(f"Received text: {data}")  # Example: print it to the console
                res = call_open_api(data)
                # Optionally, send a response back to the client
                collected_chunks = []
                collected_messages = []
                # iterate through the stream of events
                for chunk in res:
                    chunk_time = time.time() - start_time  # calculate the time delay of the chunk
                    collected_chunks.append(chunk)  # save the event response
                    chunk_message = chunk.choices[0].delta.content  # extract the message
                    collected_messages.append(chunk_message)  # save the message
                    
                    
                    if chunk_message is not None and chunk_message.find('.') != -1:
                        print("Found full stop")
                        message = [m for m in collected_messages if m is not None]
                        full_reply_content = ''.join([m for m in message])

                        await manager.send_text(full_reply_content, websocket)
                        collected_messages = []
                    

                    print(f"Message received {chunk_time:.2f} seconds after request: {chunk_message}")  # print the delay and text

                 # print the time delay and text received
                # print(f"Full response received {chunk_time:.2f} seconds after request")
                # # clean None in collected_messages
                # collected_messages = [m for m in collected_messages if m is not None]
                # full_reply_content = ''.join([m for m in collected_messages])
                #check if collected_messages is not empty
                if len(collected_messages) > 0:
                    message = [m for m in collected_messages if m is not None]
                    full_reply_content = ''.join([m for m in message])

                    await manager.send_text(full_reply_content, websocket)
                    collected_messages = []
                
            except WebSocketDisconnect:
                manager.disconnect(websocket)
                break
            except Exception as e:
                # Handle other exceptions
                print(f"Error: {str(e)}")
                break
    finally:
        manager.disconnect(websocket)

# api to acces htmlpage call voice.html
@app.get("/")
async def get():
    return FileResponse("voice_frontend.html")