def load_custom_css():
    return """
        <style>
        /* Main container styling */
        .main {
            padding: 2rem;
            max-width: 1200px;
            margin: 0 auto;
        }
        
        /* Header styling */
        h1 {
            color: #1f77b4;
            text-align: center;
            margin-bottom: 1rem;
        }
        
        /* Button styling */
        .stButton>button {
            width: 100%;
            height: 3em;
            margin-top: 1em;
            background-color: #1f77b4;
            color: white;
            border: none;
            border-radius: 0.3rem;
            transition: all 0.3s ease;
        }
        
        .stButton>button:hover {
            background-color: #155987;
            transform: translateY(-2px);
        }
        
        /* Card styling */
        .metric-card {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 1rem 0;
        }
        
        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 2rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 3rem;
            white-space: pre-wrap;
            background-color: #f8f9fa;
            border-radius: 0.3rem;
        }
        
        /* Form input styling */
        .stTextInput>div>div>input {
            background-color: #f8f9fa;
        }
        
        /* Success message styling */
        .success-message {
            padding: 1rem;
            background-color: #d4edda;
            color: #155724;
            border-radius: 0.3rem;
            margin: 1rem 0;
            text-align: center;
        }
        
        /* Error message styling */
        .error-message {
            padding: 1rem;
            background-color: #f8d7da;
            color: #721c24;
            border-radius: 0.3rem;
            margin: 1rem 0;
            text-align: center;
        }
        </style>
    """ 