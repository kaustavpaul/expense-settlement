"""
Streamlit Expense Settlement App

A multi-user expense tracking application that calculates settlements between participants.
This application is designed to be robust, user-friendly, and portable.
"""

import streamlit as st
import pandas as pd
from collections import defaultdict
from io import BytesIO

# -----------------------------------------------------------------------------
# --- Core Logic Functions ---
# -----------------------------------------------------------------------------

def get_participant_data(row, max_participants):
    """
    Extract participant data from a DataFrame row.
    
    Args:
        row: DataFrame row containing expense data
        max_participants: Maximum number of participants to check
        
    Returns:
        tuple: (total_heads, involved_participants)
    """
    total_heads = 0
    involved_participants = []
    
    for i in range(1, max_participants + 1):
        name_col = f'Participant {i} Name'
        count_col = f'Participant {i} Members'
        
        if name_col in row and pd.notna(row[name_col]) and str(row[name_col]).strip():
            participant = str(row[name_col]).strip()
            count = int(row.get(count_col, 1))
            total_heads += count
            involved_participants.append((participant, count))
    
    return total_heads, involved_participants

def calculate_settlement(expenses_df):
    """
    Calculates the settlement plan based on the expenses DataFrame.

    This function determines who owes money to whom by tracking the balance for
    each person. A positive balance means they are owed money, and a negative
    balance means they owe money. It then generates a list of transactions
    to clear these debts.

    Args:
        expenses_df (pd.DataFrame): DataFrame containing the expense records.

    Returns:
        str: A multi-line string describing the payments needed to settle up.
    """
    # Return early if there's nothing to calculate
    if expenses_df.empty or expenses_df['Amount'].sum() == 0:
        return "Enter some expenses to calculate a settlement."

    # Calculate balances
    balances = defaultdict(float)
    involved_people = set(expenses_df['Payer'].dropna())
    
    # Get all participant names
    participant_cols = [col for col in expenses_df.columns if 'Name' in col]
    for col in participant_cols:
        involved_people.update(expenses_df[col].dropna())

    # Initialize balances
    for person in involved_people:
        balances[person] = 0.0

    # Process each expense
    max_participants = (len(expenses_df.columns) - 3) // 2
    for index, row in expenses_df.iterrows():
        try:
            payer = str(row['Payer']).strip()
            amount = float(row['Amount'])

            if pd.isna(payer) or amount <= 0:
                continue

            total_heads, involved_participants = get_participant_data(row, max_participants)

            if total_heads > 0:
                cost_per_head = amount / total_heads
                balances[payer] += amount
                for participant, count in involved_participants:
                    balances[participant] -= cost_per_head * count

        except (ValueError, TypeError):
            st.warning(f"Warning: Skipping invalid data in row {index + 1}.")
            continue

    # Generate settlement plan
    owes = sorted([(p, b) for p, b in balances.items() if b < -0.01], key=lambda x: x[1])
    gets = sorted([(p, b) for p, b in balances.items() if b > 0.01], key=lambda x: -x[1])
    
    settlements = []
    i, j = 0, 0
    while i < len(owes) and j < len(gets):
        owe_p, owe_amt = owes[i]
        get_p, get_amt = gets[j]
        settle_amt = min(abs(owe_amt), get_amt)

        settlements.append(f"{owe_p} pays {get_p}: ${settle_amt:.2f}")

        owes[i] = (owe_p, owe_amt + settle_amt)
        gets[j] = (get_p, get_amt - settle_amt)

        if abs(owes[i][1]) < 0.01: i += 1
        if abs(gets[j][1]) < 0.01: j += 1

    return "\n".join(settlements) if settlements else "Everyone is settled up!"

def create_empty_dataframe(num_participants):
    """Creates an empty DataFrame with the specified number of participant columns."""
    columns = ["Expense Type", "Payer", "Amount"]
    for i in range(1, num_participants + 1):
        columns.extend([f"Participant {i} Name", f"Participant {i} Members"])
    return pd.DataFrame(columns=columns)

def parse_names(name_string):
    """Parses a comma-separated string of names into a cleaned, sorted, unique list."""
    if not isinstance(name_string, str) or not name_string.strip():
        return []
    # Split, strip whitespace, filter out empty strings, get unique names, and sort
    return sorted(list(set([name.strip() for name in name_string.split(',') if name.strip()])))

def generate_summary(df, all_people, num_participants):
    """Generates a financial summary DataFrame."""
    if df.empty or not all_people:
        return pd.DataFrame(index=["Total Paid", "Total Owed", "Difference"], 
                          columns=all_people).fillna(0.0)

    # Initialize totals
    total_paid = {p: 0.0 for p in all_people}
    total_owed = {p: 0.0 for p in all_people}

    # Calculate total paid
    paid_summary = df.groupby('Payer')['Amount'].sum()
    for person, amount in paid_summary.items():
        if person in total_paid:
            total_paid[person] = amount

    # Calculate total owed
    for _, row in df.iterrows():
        try:
            amount = float(row.get('Amount', 0))
            if pd.isna(amount) or amount <= 0:
                continue

            total_heads, involved_participants = get_participant_data(row, num_participants)

            if total_heads > 0:
                cost_per_head = amount / total_heads
                for participant, count in involved_participants:
                    if participant in total_owed:
                        total_owed[participant] += cost_per_head * count
        except (ValueError, TypeError):
            continue

    # Create summary DataFrame
    summary_df = pd.DataFrame([total_paid, total_owed], 
                            index=['Total Paid', 'Total Owed']).reindex(all_people, axis=1).fillna(0)
    summary_df.loc['Difference'] = summary_df.loc['Total Paid'] - summary_df.loc['Total Owed']
    
    return summary_df

def to_excel(df):
    """Converts a DataFrame to an Excel file in memory, with error handling."""
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer: # type: ignore
            df.to_excel(writer, index=True, sheet_name='Report')
        return output.getvalue()
    except Exception as e:
        st.error(f"Failed to create Excel file: {e}")
        return None

# -----------------------------------------------------------------------------
# --- UI Component Functions ---
# -----------------------------------------------------------------------------

def initialize_state():
    """Initializes all required session state variables in a single location."""
    defaults = {
        'num_participants': 2,
        'expenses_df': create_empty_dataframe(1),
        'show_settlement': False,
        'settlement_result': "",
        'payer_names_input': "",
        'participant_names_input': "",
        'report_finalized': False
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def display_sidebar():
    """Renders the sidebar, which is the main control hub for the app."""
    is_finalized = st.session_state.report_finalized
    with st.sidebar:
        st.header("👥 People Configuration")
        st.text_area("Payer Names (comma-separated)", key="payer_names_input", 
                     placeholder="E.g., Alice, Bob", disabled=is_finalized)
        st.text_area("Participant Names (comma-separated)", key="participant_names_input", 
                     placeholder="E.g., Alice, Bob, Charlie", disabled=is_finalized)

        payer_list = parse_names(st.session_state.payer_names_input)
        participant_list = parse_names(st.session_state.participant_names_input)
        
        st.subheader("Configured People")
        st.markdown(f"**Payers:** _{', '.join(payer_list) if payer_list else 'None'}_")
        st.markdown(f"**Participants:** _{', '.join(participant_list) if participant_list else 'None'}_")

        st.divider()
        st.header("⚙️ App Controls")
        
        # Reset App button
        st.markdown('<div class="red-button">', unsafe_allow_html=True)
        if st.button("💣 Reset App", help="Clear all names, expenses, and results.", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.toast("App has been reset!", icon="🎉")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Help Section
        with st.expander("❓ How to Use This App"):
            try:
                with open("HELP.md", "r", encoding="utf-8") as f:
                    st.markdown(f.read(), unsafe_allow_html=True)
            except FileNotFoundError:
                st.warning("HELP.md file not found.")
            except Exception as e:
                st.error(f"Error reading help file: {e}")

        return payer_list, participant_list

def display_expense_form(payer_list, participant_list):
    """Renders the dynamic form for adding a new expense."""
    st.header("📝 Add a New Expense")
    st.write("Use the buttons below to adjust the number of participants sharing this expense.")

    # Participant add/remove controls
    col1, col2, col3, _ = st.columns([1, 1.2, 2, 2.8])
    with col1:
        if st.button("➕ Add", help="Add another participant input."):
            if st.session_state.num_participants < 10:
                st.session_state.num_participants += 1
    with col2:
        if st.button("➖ Remove", help="Remove the last participant input."):
            if st.session_state.num_participants > 1:
                st.session_state.num_participants -= 1
    with col3:
        st.metric("Sharing Between", f"{st.session_state.num_participants} participants")

    # The main expense entry form
    with st.form("expense_form", clear_on_submit=True):
        st.subheader("Expense Details")
        col1, col2, col3 = st.columns([2, 1, 2])
        with col1:
            expense_type = st.text_input("Expense Type", placeholder="E.g., Dinner, Gas")
        with col2:
            amount = st.number_input("Amount", min_value=0.01, format="%.2f", step=0.01)
        with col3:
            payer = st.selectbox("Payer", options=payer_list, index=None, placeholder="Who paid?")

        st.subheader("Participants")
        participant_inputs = {}
        for i in range(1, st.session_state.num_participants + 1):
            cols = st.columns([3, 1])
            with cols[0]:
                participant_inputs[f'p_name_{i}'] = st.selectbox(
                    f"P{i} Name", options=participant_list, index=None, key=f'p_name_{i}')
            with cols[1]:
                participant_inputs[f'p_members_{i}'] = st.number_input(
                    f"P{i} Members", min_value=0, max_value=9, value=1, key=f'p_members_{i}')

        st.markdown('<div class="green-button">', unsafe_allow_html=True)
        submitted = st.form_submit_button("Add Expense")
        st.markdown('</div>', unsafe_allow_html=True)

    if submitted:
        # Form submission logic
        if not payer or not expense_type or amount <= 0:
            st.warning("Please fill out Expense Type, Amount, and Payer.")
        else:
            new_expense_data = {"Expense Type": expense_type, "Payer": payer, "Amount": amount}
            has_participants = any(participant_inputs.get(f'p_name_{i}') for i in range(1, st.session_state.num_participants + 1))
            if not has_participants:
                st.error("An expense must have at least one participant.")
            else:
                for i in range(1, st.session_state.num_participants + 1):
                    p_name = participant_inputs.get(f'p_name_{i}')
                    if p_name:
                        new_expense_data[f'Participant {i} Name'] = p_name
                        new_expense_data[f'Participant {i} Members'] = participant_inputs.get(f'p_members_{i}')
                st.session_state.expenses_df = pd.concat(
                    [st.session_state.expenses_df, pd.DataFrame([new_expense_data])], 
                    ignore_index=True)
                st.toast("Expense added!", icon="✔️")

def display_results_and_summary(all_people):
    """Renders all the data tables, export buttons, and finalization controls."""
    is_finalized = st.session_state.report_finalized

    # --- Entered Expenses Section ---
    st.header("🧾 Entered Expenses")
    if not st.session_state.expenses_df.empty:
        if is_finalized:
            excel_data = to_excel(st.session_state.expenses_df)
            if excel_data:
                st.download_button(label="📥 Export Expenses to Excel", data=excel_data,
                                  file_name="expense_report.xlsx", use_container_width=True)
        
        df_display = st.session_state.expenses_df.copy()
        if not is_finalized:
            df_display.insert(0, "Delete", False)
        
        edited_df = st.data_editor(df_display, use_container_width=True, hide_index=True, 
                                   key="expense_display_editor", disabled=is_finalized)
        
        if not is_finalized and "Delete" in edited_df.columns:
            rows_to_delete = edited_df[edited_df["Delete"]].index.tolist()
            if rows_to_delete:
                st.markdown('<div class="red-button">', unsafe_allow_html=True)
                if st.button(f"Delete {len(rows_to_delete)} expense(s)", use_container_width=True):
                    st.session_state.expenses_df = st.session_state.expenses_df.drop(rows_to_delete).reset_index(drop=True)
                    st.toast(f"{len(rows_to_delete)} expense(s) deleted.", icon="🗑️")
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("No expenses added yet. Use the form above.")

    # --- Financial Summary Section ---
    st.header("📈 Live Financial Summary")
    cleaned_df = st.session_state.expenses_df.dropna(subset=['Payer', 'Amount'], how='any').query('Amount > 0')
    
    if not cleaned_df.empty and all_people:
        summary_df = generate_summary(cleaned_df, all_people, st.session_state.num_participants)
        if is_finalized:
            excel_data = to_excel(summary_df)
            if excel_data:
                st.download_button(label="📥 Export Summary to Excel", data=excel_data,
                                  file_name="financial_summary.xlsx", use_container_width=True)
        
        summary_df['Check'] = summary_df.sum(axis=1)
        st.dataframe(summary_df.style.format("${:,.2f}", na_rep='-'), use_container_width=True)
    else:
        st.info("Enter valid expenses to see the financial summary.")

    # --- Finalize and Settlement Section ---
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

        st.divider()
        st.header("🔒 Finalize Report")
        st.warning("Finalizing the report will lock all inputs and enable exports. This cannot be undone.")
        st.markdown('<div class="red-button">', unsafe_allow_html=True)
        if st.button("🚨 Finalize and Lock Report", use_container_width=True):
            st.session_state.report_finalized = True
            st.toast("Report Finalized!", icon="🔒")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.header("✅ Report Finalized")
        st.success("The report is locked. You can now export the data or reset the app.")
    
    if st.session_state.show_settlement and not is_finalized:
        st.text_area("Settlement Plan:", value=st.session_state.settlement_result, height=150, disabled=True)
    elif not is_finalized:
        st.info("Click 'Calculate Settlement' to generate the payment plan.")

# -----------------------------------------------------------------------------
# --- Main Application ---
# -----------------------------------------------------------------------------

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
        is_finalized = st.session_state.report_finalized
        payer_list, participant_list = display_sidebar()
        all_people = sorted(list(set(payer_list + participant_list)))
        
        if not is_finalized:
            display_expense_form(payer_list, participant_list)
        
        display_results_and_summary(all_people)
    except Exception as e:
        st.error("An unexpected error occurred! Please reset the app or report the issue.")
        st.exception(e) # Log the full exception for debugging

if __name__ == "__main__":
    main() 