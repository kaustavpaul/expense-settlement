import streamlit as st
import pandas as pd
import json
from .utils import parse_names, to_excel, create_empty_dataframe
from .logic import calculate_settlement, generate_summary
from .storage import create_session, update_session, get_storage_status

def display_sidebar():
    """Renders the sidebar, which is the main control hub for the app."""
    with st.sidebar:
        payer_list = parse_names(st.session_state.payer_names_input)
        participant_list = parse_names(st.session_state.participant_names_input)
        
        st.header("👥 Configured People")
        st.markdown(f"**Payers:** _{', '.join(payer_list) if payer_list else 'None'}_")
        st.markdown(f"**Participants:** _{', '.join(participant_list) if participant_list else 'None'}_")

        st.divider()
        st.header("🔗 Cloud Session")
        
        # Unified Storage Status Indicator
        status = get_storage_status()
        if "Active" in status:
            st.caption(f"🟢 **{status}**")
        else:
            st.caption(f"🟡 **{status}** (Configure secrets for Cloud)")

        current_id = st.session_state.get('db_session_id')
        if current_id:
            st.success(f"Session Active")
            st.code(current_id, language=None)
            st.info("Copy the URL from your browser to share.")
            
            if st.button("💾 Save Changes to Cloud", type="primary", use_container_width=True):
                data_to_save = {
                    'payer_names_input': st.session_state.payer_names_input,
                    'participant_names_input': st.session_state.participant_names_input,
                    'num_participants': st.session_state.num_participants,
                    'expenses_data': st.session_state.expenses_df.to_dict('records')
                }
                update_session(current_id, data_to_save)
                st.toast("Session updated!", icon="☁️")
        else:
            st.info("Create a unique link to share this report.")
            if st.button("🚀 Create Shareable Link", use_container_width=True):
                data_to_save = {
                    'payer_names_input': st.session_state.payer_names_input,
                    'participant_names_input': st.session_state.participant_names_input,
                    'num_participants': st.session_state.num_participants,
                    'expenses_data': st.session_state.expenses_df.to_dict('records')
                }
                new_id = create_session(data_to_save)
                st.session_state.db_session_id = new_id
                st.query_params['session'] = new_id
                st.toast("Session created! URL updated.", icon="🔗")
                st.rerun()

        st.divider()
        st.header("💾 Local Backup")
        
        # Save State
        state_to_save = {
            'payer_names_input': st.session_state.payer_names_input,
            'participant_names_input': st.session_state.participant_names_input,
            'num_participants': st.session_state.num_participants,
            'expenses_data': st.session_state.expenses_df.to_dict('records')
        }
        st.download_button(
            label="📥 Download State",
            data=json.dumps(state_to_save, indent=2),
            file_name="expense_app_state.json",
            mime="application/json",
            help="Save your current progress to a file."
        )
        
        # Load State
        uploaded_file = st.file_uploader("📤 Load State", type=['json'], help="Restore functionality from a saved file.")
        if uploaded_file is not None:
            try:
                data = json.load(uploaded_file)
                st.session_state.payer_names_input = data.get('payer_names_input', "")
                st.session_state.participant_names_input = data.get('participant_names_input', "")
                st.session_state.num_participants = data.get('num_participants', 2)
                if 'expenses_data' in data:
                    st.session_state.expenses_df = pd.DataFrame(data['expenses_data'])
                st.toast("State loaded successfully!", icon="✅")
            except Exception as e:
                st.error(f"Error loading state: {e}")

        st.divider()
        st.header("⚙️ App Controls")
        
        # Reset App button with confirmation
        with st.popover("💣 Reset App", help="Clear all names, expenses, and results."):
            st.warning("Are you sure? This will delete all data.")
            if st.button("Confirm Reset", type="primary"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.toast("App has been reset!", icon="🎉")
                st.rerun()
        
        st.divider()
        
        # Help Section
        with st.expander("❓ How to Use This App"):
            try:
                with open("HELP.md", "r", encoding="utf-8") as f:
                    st.markdown(f.read(), unsafe_allow_html=True)
            except:
                st.warning("Help file not found.")

        return payer_list, participant_list

def display_people_configuration():
    """Renders the people configuration inputs at the top of the main page."""
    is_finalized = st.session_state.report_finalized
    
    with st.expander("👥 People Configuration", expanded=not (st.session_state.payer_names_input and st.session_state.participant_names_input)):
        col1, col2 = st.columns(2)
        with col1:
            st.text_area("Payer Names (comma-separated)", key="payer_names_input", 
                         placeholder="E.g., Alice, Bob", disabled=is_finalized, help="People who can pay for expenses.")
        with col2:
            st.text_area("Participant Names (comma-separated)", key="participant_names_input", 
                         placeholder="E.g., Alice, Bob, Charlie", disabled=is_finalized, help="People who share the expenses.")

def display_expense_form(payer_list, participant_list):
    """Renders the detailed form for adding a new expense (supporting head counts)."""
    with st.form("expense_form", clear_on_submit=True):
        st.subheader("Expense Details")
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            expense_type = st.text_input("Expense Type", placeholder="E.g., Dinner, Gas")
        with col2:
            amount = st.number_input("Amount", min_value=0.01, format="%.2f", step=0.01)
        with col3:
            payer = st.selectbox("Payer", options=payer_list, index=None, placeholder="Who paid?")

        st.subheader("Participants (Advanced)")
        st.caption("Add participants and specify head counts (e.g., for families).")
        
        # Dynamic participant inputs based on slider or number input
        num_inputs = st.number_input("Number of Participant Slots", min_value=1, max_value=20, value=st.session_state.num_participants)
        
        participant_inputs = {}
        for i in range(1, num_inputs + 1):
            cols = st.columns([3, 1])
            with cols[0]:
                participant_inputs[f'p_name_{i}'] = st.selectbox(
                    f"P{i} Name", options=participant_list, index=None, key=f'form_p_name_{i}')
            with cols[1]:
                participant_inputs[f'p_members_{i}'] = st.number_input(
                    f"P{i} Members", min_value=0, max_value=9, value=1, key=f'form_p_members_{i}')

        st.markdown('<div class="green-button">', unsafe_allow_html=True)
        submitted = st.form_submit_button("Add Expense")
        st.markdown('</div>', unsafe_allow_html=True)

    if submitted:
        if not payer or not expense_type or amount <= 0:
            st.warning("Please fill out Expense Type, Amount, and Payer.")
        else:
            new_expense_data = {"Expense Type": expense_type, "Payer": payer, "Amount": amount}
            has_participants = False
            for i in range(1, num_inputs + 1):
                p_name = participant_inputs.get(f'p_name_{i}')
                if p_name:
                    has_participants = True
                    new_expense_data[f'Participant {i} Name'] = p_name
                    new_expense_data[f'Participant {i} Members'] = participant_inputs.get(f'p_members_{i}')
            
            if not has_participants:
                st.error("An expense must have at least one participant.")
            else:
                st.session_state.expenses_df = pd.concat(
                    [st.session_state.expenses_df, pd.DataFrame([new_expense_data])], 
                    ignore_index=True)
                st.toast("Expense added via Form!", icon="✔️")

def display_expense_editor(payer_list, participant_list):
    """Renders the expense editor with Detailed (Form) and Quick (Grid) tabs."""
    st.header("📝 Add Expenses")
    
    tab1, tab2 = st.tabs(["📋 Detailed Entry (Form)", "⚡ Quick Entry (Grid)"])
    
    with tab1:
        display_expense_form(payer_list, participant_list)

    with tab2:
        st.info("Use this grid for simple expenses where everyone has a head count of 1. Multi-select participants in the 'Participants' column.")
        
        # Ensure dataframe has correct columns for Grid
        current_df = st.session_state.expenses_df
        required_cols = ["Expense Type", "Payer", "Amount", "Participants"]
        
        # Add missing columns
        for col in required_cols:
            if col not in current_df.columns:
                current_df[col] = None
        
        # Configure columns for editor
        column_config = {
            "Expense Type": st.column_config.TextColumn("Type", required=True),
            "Payer": st.column_config.SelectboxColumn("Payer", options=payer_list, required=True),
            "Amount": st.column_config.NumberColumn("Amount", min_value=0.01, format="$%.2f", required=True),
            "Participants": st.column_config.ListColumn(
                "Participants", 
                help="Select all who shared this expense.",
                width="large"
            )
        }
        
        # Let's show the main columns + Participants. Hide detailed columns to avoid clutter.
        visible_cols = ["Expense Type", "Payer", "Amount", "Participants"]
        
        edited_df = st.data_editor(
            current_df,
            key="expense_editor",
            num_rows="dynamic",
            use_container_width=True,
            column_config=column_config,
            column_order=visible_cols, # Only show these, others are hidden but preserved
            hide_index=True
        )
        
        # Update Session State
        if not edited_df.equals(current_df):
            st.session_state.expenses_df = edited_df

def display_expense_log():
    """Renders a collapsible log of all entered expenses."""
    with st.expander("📋 Expense Log", expanded=False):
        df = st.session_state.expenses_df
        if not df.empty:
            # Format the display dataframe for readability
            display_df = df.copy()
            
            # 1. Handle List-based Participants (from Grid)
            if 'Participants' in display_df.columns:
                display_df['Participants'] = display_df['Participants'].apply(
                    lambda x: ", ".join(x) if isinstance(x, list) else x
                )
            
            # 2. Handle Legacy Participant columns (from Form)
            # Find all Participant N Name columns
            p_cols = [c for c in display_df.columns if "Participant" in c and "Name" in c]
            if p_cols:
                # We could consolidate these for the log
                def aggregate_participants(row):
                    parts = []
                    # Check list column first
                    if 'Participants' in row and row['Participants']:
                        parts.append(str(row['Participants']))
                    # Check legacy columns
                    for col in p_cols:
                        if pd.notna(row[col]):
                            mem_col = col.replace("Name", "Members")
                            mem_count = row.get(mem_col, 1)
                            parts.append(f"{row[col]} (x{int(mem_count)})" if mem_count != 1 else row[col])
                    return ", ".join(parts)

                display_df['All Participants'] = display_df.apply(aggregate_participants, axis=1)
                # Show only core columns for the log
                core_cols = ["Expense Type", "Payer", "Amount", "All Participants"]
                # Keep only those that exist
                final_cols = [c for c in core_cols if c in display_df.columns]
                st.dataframe(display_df[final_cols], use_container_width=True, hide_index=True)
            else:
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No expenses entered yet.")

def display_results_and_summary(all_people):
    """Renders all the data tables, export buttons, and finalization controls."""
    is_finalized = st.session_state.report_finalized

    # --- Financial Summary Section ---
    st.header("📈 Live Financial Summary")
    cleaned_df = st.session_state.expenses_df.dropna(subset=['Payer', 'Amount'], how='any').copy()
    cleaned_df = cleaned_df[cleaned_df['Amount'] > 0]
    
    if not cleaned_df.empty and all_people:
        summary_df = generate_summary(cleaned_df, all_people, st.session_state.num_participants)
        
        # Add total row check
        summary_df['Check'] = summary_df.sum(axis=1)
        
        # Display with formatting
        st.dataframe(summary_df.style.format("${:,.2f}", na_rep='-'), use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
             if st.button("📥 Export Summary"):
                excel_data = to_excel(summary_df)
                if excel_data:
                    st.download_button(label="Download Excel", data=excel_data,
                                    file_name="financial_summary.xlsx", use_container_width=True)

    else:
        st.info("Enter valid expenses to see the financial summary.")

    # --- Finalize and Settlement Section ---
    st.divider()
    if not is_finalized:
        st.header("💳 Final Settlement")
        col1, col2, _ = st.columns([1, 1, 4])
        with col1:
            st.markdown('<div class="green-button">', unsafe_allow_html=True)
            if st.button("✅ Calculate Settlement", use_container_width=True):
                st.session_state.settlement_result = calculate_settlement(cleaned_df)
                st.session_state.show_settlement = True
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="red-button">', unsafe_allow_html=True)
            if st.button("🗑️ Reset Calculation", use_container_width=True):
                st.session_state.show_settlement = False
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    
    if st.session_state.show_settlement:
        st.text_area("Settlement Plan:", value=st.session_state.settlement_result, height=150, disabled=True)
