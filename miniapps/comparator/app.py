import streamlit as st
import pandas as pd
import numpy as np
import yaml
import os
import random
from typing import Dict, List, Tuple

def load_test_data():
    """Load test data from YAML file"""
    try:
        with open('test_data.yaml', 'r') as file:
            data = yaml.safe_load(file)
            return data.get('choices', []), data.get('criteria', [])
    except FileNotFoundError:
        return [], []

def generate_random_data(choices: List[str], criteria: List[str]) -> Dict:
    """Generate random grades and notes for testing"""
    matrix_data = {}
    
    # Sample notes for variety
    sample_notes = [
        "Excellent performance in this area",
        "Good but could be better",
        "Average performance",
        "Below average",
        "Outstanding quality",
        "Meets expectations",
        "Exceeds expectations",
        "Needs improvement",
        "Top tier option",
        "Competitive choice"
    ]
    
    for choice in choices:
        for criteria_item in criteria:
            # Random grade (1-10)
            grade_key = f"grade_{choice}_{criteria_item}"
            matrix_data[grade_key] = random.randint(1, 10)
            
            # Random notes
            notes_key = f"notes_{choice}_{criteria_item}"
            matrix_data[notes_key] = random.choice(sample_notes)
    
    return matrix_data

def main():
    st.set_page_config(
        page_title="Decision Matrix Comparator",
        page_icon="⚖️",
        layout="wide"
    )
    
    st.title("⚖️ Decision Matrix Comparator")
    st.markdown("Compare multiple choices against various criteria to make better decisions!")
    
    # Environment variable for default data
    use_default_data = os.getenv('USE_DEFAULT_DATA', 'true').lower() == 'true'
    
    # Initialize session state
    if 'choices' not in st.session_state:
        st.session_state.choices = []
    if 'criteria' not in st.session_state:
        st.session_state.criteria = []
    if 'matrix_data' not in st.session_state:
        st.session_state.matrix_data = {}
    if 'pivot_view' not in st.session_state:
        st.session_state.pivot_view = False
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    
    # Add default test data on first load
    if not st.session_state.initialized and use_default_data:
        # Try to load from YAML first
        yaml_choices, yaml_criteria = load_test_data()
        
        if yaml_choices and yaml_criteria:
            # Use YAML data and generate random grades/notes
            st.session_state.choices = yaml_choices
            st.session_state.criteria = yaml_criteria
            st.session_state.matrix_data = generate_random_data(yaml_choices, yaml_criteria)
        else:
            # Fallback to original default data
            st.session_state.choices = ["vinfast", "yadea"]
            st.session_state.criteria = ["speed", "price"]
        
        st.session_state.initialized = True
    
    # Sidebar for input
    with st.sidebar:
        st.header("📝 Input Data")
        
        # Load test data button
        if st.button("📊 Load Test Data"):
            yaml_choices, yaml_criteria = load_test_data()
            if yaml_choices and yaml_criteria:
                st.session_state.choices = yaml_choices
                st.session_state.criteria = yaml_criteria
                st.session_state.matrix_data = generate_random_data(yaml_choices, yaml_criteria)
                st.rerun()
            else:
                st.error("No test data found in test_data.yaml")
        
        # Choices input
        st.subheader("Choices")
        new_choice = st.text_input("Add a choice:", key="choice_input")
        if st.button("Add Choice") and new_choice:
            if new_choice not in st.session_state.choices:
                st.session_state.choices.append(new_choice)
                st.rerun()
        
        # Display and manage choices
        if st.session_state.choices:
            st.write("**Current Choices:**")
            for i, choice in enumerate(st.session_state.choices):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"• {choice}")
                with col2:
                    if st.button("🗑️", key=f"del_choice_{i}"):
                        st.session_state.choices.pop(i)
                        # Remove from matrix data
                        for criteria in st.session_state.criteria:
                            key = f"{choice}_{criteria}"
                            if key in st.session_state.matrix_data:
                                del st.session_state.matrix_data[key]
                        st.rerun()
        
        st.divider()
        
        # Criteria input
        st.subheader("Criteria")
        new_criteria = st.text_input("Add a criteria:", key="criteria_input")
        if st.button("Add Criteria") and new_criteria:
            if new_criteria not in st.session_state.criteria:
                st.session_state.criteria.append(new_criteria)
                st.rerun()
        
        # Display and manage criteria
        if st.session_state.criteria:
            st.write("**Current Criteria:**")
            for i, criteria in enumerate(st.session_state.criteria):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"• {criteria}")
                with col2:
                    if st.button("🗑️", key=f"del_criteria_{i}"):
                        st.session_state.criteria.pop(i)
                        # Remove from matrix data
                        for choice in st.session_state.choices:
                            key = f"{choice}_{criteria}"
                            if key in st.session_state.matrix_data:
                                del st.session_state.matrix_data[key]
                        st.rerun()
        
        st.divider()
        
        # Pivot button
        if st.session_state.choices and st.session_state.criteria:
            if st.button("🔄 Pivot View"):
                st.session_state.pivot_view = not st.session_state.pivot_view
                st.rerun()
            
            # Clear all data
            if st.button("🗑️ Clear All Data"):
                st.session_state.choices = []
                st.session_state.criteria = []
                st.session_state.matrix_data = {}
                st.rerun()
    
    # Main content area
    if not st.session_state.choices or not st.session_state.criteria:
        st.info("👈 Add some choices and criteria in the sidebar to get started!")
        return
    
    # Matrix input section
    st.header("📊 Decision Matrix")
    
    if st.session_state.pivot_view:
        # Pivoted view: Criteria as rows, Choices as columns
        st.subheader("Criteria vs Choices")
        
        for criteria in st.session_state.criteria:
            st.write(f"**{criteria}**")
            cols = st.columns(len(st.session_state.choices))
            
            for i, choice in enumerate(st.session_state.choices):
                with cols[i]:
                    st.write(f"**{choice}**")
                    
                    # Grade input
                    grade_key = f"grade_{choice}_{criteria}"
                    grade = st.number_input(
                        "Grade (1-10):",
                        min_value=1,
                        max_value=10,
                        value=st.session_state.matrix_data.get(grade_key, 5),
                        key=grade_key
                    )
                    st.session_state.matrix_data[grade_key] = grade
                    
                    # Notes input
                    notes_key = f"notes_{choice}_{criteria}"
                    notes = st.text_area(
                        "Notes:",
                        value=st.session_state.matrix_data.get(notes_key, ""),
                        key=notes_key,
                        height=100
                    )
                    st.session_state.matrix_data[notes_key] = notes
    else:
        # Normal view: Choices as rows, Criteria as columns
        st.subheader("Choices vs Criteria")
        
        for choice in st.session_state.choices:
            st.write(f"**{choice}**")
            cols = st.columns(len(st.session_state.criteria))
            
            for i, criteria in enumerate(st.session_state.criteria):
                with cols[i]:
                    st.write(f"**{criteria}**")
                    
                    # Grade input
                    grade_key = f"grade_{choice}_{criteria}"
                    grade = st.number_input(
                        "Grade (1-10):",
                        min_value=1,
                        max_value=10,
                        value=st.session_state.matrix_data.get(grade_key, 5),
                        key=grade_key
                    )
                    st.session_state.matrix_data[grade_key] = grade
                    
                    # Notes input
                    notes_key = f"notes_{choice}_{criteria}"
                    notes = st.text_area(
                        "Notes:",
                        value=st.session_state.matrix_data.get(notes_key, ""),
                        key=notes_key,
                        height=100
                    )
                    st.session_state.matrix_data[notes_key] = notes
    
    # Results section
    st.header("📈 Analysis Results")
    
    # Create DataFrame for analysis
    if st.session_state.matrix_data:
        data = []
        for choice in st.session_state.choices:
            row = {'Choice': choice}
            total_score = 0
            for criteria in st.session_state.criteria:
                grade_key = f"grade_{choice}_{criteria}"
                grade = st.session_state.matrix_data.get(grade_key, 5)
                row[criteria] = grade
                total_score += grade
            
            row['Total Score'] = total_score
            row['Average Score'] = round(total_score / len(st.session_state.criteria), 2)
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Display results
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Scores Matrix")
            st.dataframe(df.set_index('Choice'), use_container_width=True)
        
        with col2:
            st.subheader("🏆 Rankings")
            # Sort by total score
            ranked_df = df.sort_values('Total Score', ascending=False)
            for i, (_, row) in enumerate(ranked_df.iterrows()):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "📊"
                st.write(f"{medal} **{row['Choice']}**: {row['Total Score']} pts (avg: {row['Average Score']})")
        
        # Detailed notes section
        st.subheader("📝 Detailed Notes")
        for choice in st.session_state.choices:
            with st.expander(f"Notes for {choice}"):
                for criteria in st.session_state.criteria:
                    notes_key = f"notes_{choice}_{criteria}"
                    notes = st.session_state.matrix_data.get(notes_key, "")
                    if notes:
                        st.write(f"**{criteria}**: {notes}")

if __name__ == "__main__":
    main() 