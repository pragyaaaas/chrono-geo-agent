import os
from dotenv import load_dotenv
load_dotenv()

# --- Core Components ---
from agent_core.modules.messages import Messages
from agent_core.agents.assistant_agent import AssistantAgent
from agent_core.teams.single_agent import SingleAgent
from llm_clients.openai_client import GroqClient

# --- Data & Tools ---
from geoapps.geeo.data_manager import DataManager
from geoapps.geeo.database import Database
from geoapps.geeo.map_tools import MapTools
from geoapps.geeo.data_tools import DataTools
from geoapps.geeo.vision import Vision
from geoapps.change_detection.change_detection_tools import ChangeDetectionTools

# --- UI ---
from ui.dash_ui import UI 

if __name__ == "__main__":
    
    print("Setting up Geo-Sentinel backend...")

    model_client = GroqClient(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        api_key=os.environ.get("GROQ_API_KEY"),
        temperature=0.1
    )

    data_manager = DataManager()
    
    # Initialize toolsets
    messages = Messages()
    database = Database(data_manager)
    vision = Vision(data_manager) 
    map_tools = MapTools(data_manager, vision, map_style="open-street-map")
    data_tools = DataTools(data_manager, vision)
    change_detection_tool = ChangeDetectionTools(data_manager)
    
    single_agent = SingleAgent(
        name="single_agent",
        model_client=model_client,
        messages=messages,
        toolsets_list=[database, vision, map_tools, data_tools, change_detection_tool],
        system_message="You are Geo-Sentinel, a defense GEOINT agent."
    )
    
    print("Backend setup complete. Initializing UI...")
    
    class Placeholder:
        def __init__(self): self.models = {}

    ui_app = UI(
        data_memory=data_manager, 
        model_zoo=Placeholder(),
        map_ops=map_tools,
        detection_obj=vision,
        data_analytics=Placeholder(),
        agent=single_agent
    )

    print("Launching Geo-Sentinel UI at http://127.0.0.1:8050/")
    # --- CRITICAL FIX: dev_tools_hot_reload=False ---
    ui_app.app.run(debug=True, dev_tools_hot_reload=False, port=8050)