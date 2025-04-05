import streamlit as st
from history_manager import HistoryManager
import plotly.express as px
import pandas as pd
from datetime import datetime

def render_history_page():
    st.title("Question Paper History")
    
    # Initialize history manager
    history_manager = HistoryManager()
    
    # Sidebar filters
    st.sidebar.header("Filters")
    search_query = st.sidebar.text_input("Search by subject/topic")
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(datetime.now().date(), datetime.now().date())
    )
    
    # Get statistics
    stats = history_manager.get_statistics()
    
    # Show statistics in expandable section
    with st.expander("📊 Statistics", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Papers", stats['total_papers'])
            st.metric("Average Marks", f"{stats['average_marks']:.1f}")
        
        with col2:
            # Create pie chart for subjects
            if stats['papers_by_subject']:
                df_subjects = pd.DataFrame({
                    'Subject': list(stats['papers_by_subject'].keys()),
                    'Count': list(stats['papers_by_subject'].values())
                })
                fig_subjects = px.pie(
                    df_subjects,
                    values='Count',
                    names='Subject',
                    title="Papers by Subject"
                )
                st.plotly_chart(fig_subjects, use_container_width=True)
            else:
                st.info("No subject data available")
        
        with col3:
            # Create bar chart for difficulty levels
            if stats['papers_by_difficulty']:
                df_difficulty = pd.DataFrame({
                    'Difficulty': list(stats['papers_by_difficulty'].keys()),
                    'Count': list(stats['papers_by_difficulty'].values())
                })
                fig_difficulty = px.bar(
                    df_difficulty,
                    x='Difficulty',
                    y='Count',
                    title="Papers by Difficulty",
                    color='Difficulty',
                    color_discrete_map={
                        'Easy': '#2ecc71',
                        'Medium': '#f1c40f',
                        'Hard': '#e74c3c'
                    }
                )
                fig_difficulty.update_layout(
                    showlegend=False,
                    xaxis_title="",
                    yaxis_title="Number of Papers"
                )
                st.plotly_chart(fig_difficulty, use_container_width=True)
            else:
                st.info("No difficulty data available")
    
    # Get papers based on filters
    if search_query:
        papers = history_manager.search_papers(search_query)
    else:
        papers = history_manager.get_all_papers()
    
    # Filter by date range
    papers = [
        p for p in papers
        if date_range[0] <= datetime.strptime(p['timestamp'].split()[0], "%Y-%m-%d").date() <= date_range[1]
    ]
    
    # Show papers
    st.header(f"Generated Papers ({len(papers)})")
    
    if not papers:
        st.info("No papers found matching your criteria")
        return
    
    for paper in papers:
        with st.expander(f"Paper {paper['id']} - {paper['timestamp']}"):
            # Paper metadata
            st.markdown(f"""
                <div style='background-color: #f8f9fa; padding: 1rem; border-radius: 5px; margin-bottom: 1rem;'>
                    <h4 style='margin: 0; color: #2c3e50;'>Paper Details</h4>
                    <hr style='margin: 0.5rem 0;'>
                    <table style='width: 100%;'>
                        <tr>
                            <td><strong>Subject:</strong></td>
                            <td>{paper['metadata'].get('subject', 'N/A')}</td>
                            <td><strong>Topic:</strong></td>
                            <td>{paper['metadata'].get('topic', 'N/A')}</td>
                        </tr>
                        <tr>
                            <td><strong>Difficulty:</strong></td>
                            <td>{paper['metadata'].get('difficulty', 'N/A')}</td>
                            <td><strong>Total Marks:</strong></td>
                            <td>{paper['metadata'].get('total_marks', 'N/A')}</td>
                        </tr>
                    </table>
                </div>
            """, unsafe_allow_html=True)
            
            # Paper content in tabs
            tab1, tab2 = st.tabs(["📝 Question Paper", "✅ Answer Key"])
            
            with tab1:
                st.markdown(paper['questions'])
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.download_button(
                        "📄 Download Question Paper",
                        paper['questions'],
                        f"question_paper_{paper['id']}.pdf",
                        mime="application/pdf",
                        key=f"hist_q_{paper['id']}"
                    )
            
            if paper['answers']:
                with tab2:
                    st.markdown(paper['answers'])
                    st.download_button(
                        "✅ Download Answer Key",
                        paper['answers'],
                        f"answer_key_{paper['id']}.pdf",
                        mime="application/pdf",
                        key=f"hist_a_{paper['id']}"
                    )
            
            # Delete button with confirmation
            if st.button("🗑️ Delete Paper", key=f"del_{paper['id']}"):
                if st.button("⚠️ Confirm Delete", key=f"confirm_del_{paper['id']}"):
                    if history_manager.delete_paper(paper['id']):
                        st.success("Paper deleted successfully!")
                        st.experimental_rerun()

if __name__ == "__main__":
    render_history_page() 