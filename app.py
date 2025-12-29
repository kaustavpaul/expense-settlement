import streamlit as st
import pandas as pd
from src.utils import create_empty_dataframe
from src.ui import display_sidebar, display_expense_editor, display_results_and_summary, display_people_configuration, display_expense_log
from src.storage import load_session

def initialize_state():
    """Initializes all required session state variables in a single location."""
    defaults = {
        'num_participants': 2,
        'expenses_df': create_empty_dataframe(1),
        'show_settlement': False,
        'settlement_result': "",
        'payer_names_input': "",
        'participant_names_input': "",
        'report_finalized': False,
        'db_session_id': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Check for query params ONCE on startup (if we haven't already loaded a session)
    if 'session' in st.query_params and not st.session_state.db_session_id:
        session_id = st.query_params['session']
        data = load_session(session_id)
        if data:
            st.session_state.payer_names_input = data.get('payer_names_input', "")
            st.session_state.participant_names_input = data.get('participant_names_input', "")
            st.session_state.num_participants = data.get('num_participants', 2)
            if 'expenses_data' in data:
                st.session_state.expenses_df = pd.DataFrame(data['expenses_data'])
            st.session_state.db_session_id = session_id
            st.toast("Session loaded from cloud!", icon="☁️")
        else:
            st.error("Session not found or expired.")

def main():
    """Main function to run the Streamlit application."""
    st.set_page_config(page_title="Expense Settlement App", layout="wide")
    st.title("💰 Expense Settlement App")

    st.markdown("""
    <style>
        div.red-button button { background-color: #D32F2F; color: white; border: 1px solid #D32F2F; }
        div.red-button button:hover { background-color: #E57373; border: 1px solid #E57373; color: white; }
        div.green-button button { background-color: #2E7D32; color: white; border: 1px solid #2E7D32; }
        div.green-button button:hover { background-color: #66BB6A; border: 1px solid #66BB6A; color: white; }
    </style>
    """, unsafe_allow_html=True)

    try:
        initialize_state()
        
        # Sidebar & Configuration
        payer_list, participant_list = display_sidebar()
        all_people = sorted(list(set(payer_list + participant_list)))
        
        if not st.session_state.report_finalized:
            display_people_configuration()
            display_expense_editor(payer_list, participant_list)
            display_expense_log()
        else:
            st.info("Report is finalized. Editing is disabled.")
            st.dataframe(st.session_state.expenses_df)
        
        # Results
        display_results_and_summary(all_people)
        
    except Exception as e:
        st.error("An unexpected error occurred!")
        st.exception(e)

if __name__ == "__main__":
    main()