# ui/dash_ui.py
# --- ChronogeoAgent: MEMORY EDITION ---

import re
import os
import sys
import traceback
import random
from flask import send_from_directory

# --- IMPORT GEE LOGIC ---
sys.path.append(os.getcwd()) 
import gee_logic

from dash import Dash, html, dcc, Input, Output, State, no_update
from dash_extensions import Keyboard
from dash.exceptions import PreventUpdate

class UI:
    def __init__(self, data_memory, model_zoo, map_ops, detection_obj, data_analytics, agent=None):
        self.agent = agent
        self.app = self.create_app()

    def create_app(self):
        assets_path = os.path.join(os.getcwd(), 'assets')
        app = Dash(__name__, assets_folder=assets_path) 
        app.title = "ChronogeoAgent"
        
        @app.server.route('/maps/<path:filename>')
        def serve_map(filename):
            return send_from_directory(assets_path, filename)

        app.layout = self.layout()
        self.register_callbacks(app)
        return app

    def layout(self):
        return html.Div([
            
            # --- MEMORY STORAGE (Hidden) ---
            # This holds the state: {'intent': 'flood', 'location': 'kerala', 'years': []}
            dcc.Store(id='chat-memory', storage_type='memory', data={}),

            # 1. BACKGROUND MAP
            html.Div([
                html.Iframe(
                    id='gee-iframe',
                    src="", 
                    style={'width': '100vw', 'height': '100vh', 'border': 'none', 'position': 'absolute', 'top': '0', 'left': '0', 'z-index': '0'}
                )
            ]),

            # 2. FLOATING ASSISTANT
            html.Div([
                # Header
                html.Div([
                    html.Div([
                        html.Span("🌍 ", style={'margin-right': '10px', 'font-size': '1.2em'}),
                        html.Span("ChronogeoAgent", className='header-title')
                    ]),
                    html.Span("ONLINE", className='status-indicator')
                ], className='chat-header'),

                # Chat History
                html.Div(id='chat-display', children=[
                    html.Div("Hello! I am your geospatial assistant. I can help with Floods, Fires, Construction, or Deforestation.\n\nHow can I assist you today?", className='msg-bubble msg-bot')
                ], className='chat-history'),

                # Input Area
                html.Div([
                    Keyboard(
                        dcc.Input(
                            id='chat-input',
                            type='text',
                            placeholder='Type your reply...',
                            className='custom-input',
                            autoComplete='off'
                        ),
                        captureKeys=["Enter"],
                        id='chat-input-keyboard'
                    ),
                    html.Button("Send", id='chat-send', className='send-btn'),
                ], className='input-area')

            ], className='floating-card') 

        ], style={'width': '100vw', 'height': '100vh', 'overflow': 'hidden', 'position': 'relative', 'background-color': '#0b1120'})

    def register_callbacks(self, app):
        @app.callback(
            [Output('chat-display', 'children'),
             Output('chat-input', 'value'),
             Output('gee-iframe', 'src'),
             Output('chat-memory', 'data')], # Update Memory
            [Input('chat-input-keyboard', 'n_keydowns'),
             Input('chat-send', 'n_clicks')],
            [State('chat-input', 'value'),
             State('chat-display', 'children'),
             State("chat-input-keyboard", "keydown"),
             State('chat-memory', 'data')], # Read Memory
            prevent_initial_call=True
        )
        def submit_message(n_keydowns, n_clicks, message, current_children, key_event, memory_data):
            if key_event and key_event['shiftKey']: raise PreventUpdate
            if not message: raise PreventUpdate
            if (n_clicks is None or n_clicks < 1) and key_event is None: raise PreventUpdate

            if not isinstance(current_children, list): current_children = []
            if memory_data is None: memory_data = {}

            # 1. User Bubble
            user_bubble = html.Div(message, className='msg-bubble msg-user')
            new_children = current_children + [user_bubble]

            gee_map_src = no_update
            response_text = ""
            msg_lower = message.lower()
            
            # Reset keywords
            if msg_lower in ['reset', 'start over', 'clear', 'hi', 'hello']:
                memory_data = {} # Wipe memory
                response_text = "Hi! Memory cleared. What would you like to analyze now? (Flood, Fire, Urban, Forest)"
                bot_bubble = html.Div(response_text, className='msg-bubble msg-bot')
                return new_children + [bot_bubble], "", gee_map_src, memory_data

            try:
                # --- STEP 1: EXTRACT NEW INFO ---
                new_intent = None
                if "flood" in msg_lower or "water" in msg_lower: new_intent = "flood"
                elif "fire" in msg_lower or "burn" in msg_lower: new_intent = "fire"
                elif "construction" in msg_lower or "urbanization" in msg_lower or "buildings" in msg_lower: new_intent = "urban"
                elif "deforestation" in msg_lower or "clearing" in msg_lower or "forest" in msg_lower: new_intent = "forest"

                new_years = re.findall(r'\b20\d{2}\b', message)
                
                new_location = None
                # Simple heuristic to capture location if not explicitly stated with "in"
                # If message is short (e.g. "Kerala") and not a number, treat as location
                if len(message.split()) < 3 and not new_years and not new_intent:
                    new_location = message.strip()
                elif " in " in msg_lower:
                    try: new_location = message.split(" in ")[1].split(" ")[0].strip().replace("?", "")
                    except: pass
                elif " at " in msg_lower:
                    try: new_location = message.split(" at ")[1].split(" ")[0].strip().replace("?", "")
                    except: pass

                # --- STEP 2: MERGE WITH MEMORY ---
                # If user provides a new intent, it overrides the old one
                if new_intent: 
                    memory_data['intent'] = new_intent
                
                # If user provides a location, save it
                if new_location:
                    memory_data['location'] = new_location
                
                # If user provides years, save them
                if new_years:
                    memory_data['years'] = new_years

                # Retrieve current state
                current_intent = memory_data.get('intent')
                current_location = memory_data.get('location')
                current_years = memory_data.get('years', [])

                # --- STEP 3: CHECK WHAT IS MISSING ---
                
                if not current_intent:
                    response_text = "I'm not sure what to analyze. Are you interested in **Floods**, **Fires**, **Construction**, or **Deforestation**?"
                
                elif not current_location:
                    response_text = f"I can check for {current_intent}. **Where** should I look? (e.g., Kerala, Pune, California)"
                
                elif not current_years:
                    if current_intent in ["flood", "fire"]:
                        response_text = f"I found {current_location}. What **Year** did the {current_intent} happen? (e.g., 2018)"
                    else:
                        response_text = f"For {current_intent} in {current_location}, I need a timeframe. Please give me a **Start Year** and **End Year** (e.g., 2016 2021)."
                
                # --- STEP 4: EXECUTE IF COMPLETE ---
                else:
                    confirmation_phrases = ["Analyzing...", "Scanning satellite data...", "Accessing  archives..."]
                    
                    if current_intent == "flood":
                        target_year = current_years[0]
                        result, fname = gee_logic.analyze_flood_sar(current_location, target_year)
                        response_text = f"{random.choice(confirmation_phrases)}\n\n✅ Analysis Complete for {current_location} ({target_year}).\n{result}"
                    
                    elif current_intent == "fire":
                        target_year = current_years[0]
                        result, fname = gee_logic.analyze_fire_optical(current_location, target_year)
                        response_text = f"{random.choice(confirmation_phrases)}\n\n✅ Analysis Complete for {current_location} ({target_year}).\n{result}"
                    
                    elif current_intent == "urban":
                        if len(current_years) < 2:
                            response_text = "I need an END year too. (e.g. 'to 2022')"
                            fname = None
                        else:
                            result, fname = gee_logic.analyze_urbanization(current_location, current_years[0], current_years[1])
                            response_text = f"{random.choice(confirmation_phrases)}\n\n✅ Scan Complete for {current_location}.\n{result}"

                    elif current_intent == "forest":
                         if len(current_years) < 2:
                            response_text = "I need an END year too."
                            fname = None
                         else:
                            result, fname = gee_logic.analyze_deforestation(current_location, current_years[0], current_years[1])
                            response_text = f"{random.choice(confirmation_phrases)}\n\n✅ Analysis Complete for {current_location}.\n{result}"

                    # Success? Show map and Clear specific memory or keep context?
                    # Let's keep context so they can ask "What about 2019?" later if we added that logic.
                    # For now, if successful, we serve map.
                    if fname:
                        gee_map_src = f"/maps/{fname}"
                        # Optional: Clear memory after success so next query starts fresh? 
                        # Or keep it? Let's clear 'years' so they can check a different date easily.
                        memory_data['years'] = [] 

            except Exception as e:
                traceback.print_exc()
                response_text = "System Error. Please try saying 'Reset' to start over."

            bot_bubble = html.Div(dcc.Markdown(response_text), className='msg-bubble msg-bot')
            final_children = new_children + [bot_bubble]
            
            return final_children, "", gee_map_src, memory_data

    def __call__(self):
        self.app.run_server(debug=True, dev_tools_hot_reload=False)