"""
Main Streamlit Dashboard for Lead Generation - REAL PubMed Data Only
"""
from datetime import datetime
import plotly.express as px
import streamlit as st
import pandas as pd
import traceback
import json
import sys
import os

# ===== CREATE NECESSARY FOLDERS =====
os.makedirs('data/processed', exist_ok=True)
os.makedirs('data/raw', exist_ok=True)
os.makedirs('config', exist_ok=True)

# ===== CREATE DEFAULT CONFIG =====
config_path = 'config/keywords.json'
if not os.path.exists(config_path):
    default_config = {
        "search_terms": [
            "Drug-Induced Liver Injury",
            "3D cell culture",
            "organ-on-chip",
            "hepatic spheroids",
            "investigative toxicology",
            "in vitro models",
            "hepatotoxicity",
            "preclinical safety",
            "liver toxicity",
            "hepatocyte culture",
            "3D liver model",
            "toxicology screening"
        ],
        "high_score_titles": [
            "director",
            "head",
            "professor",
            "principal investigator",
            "vp",
            "chief"
        ],
        "high_score_keywords": [
            "toxicology",
            "safety",
            "hepatic",
            "liver",
            "3D",
            "in vitro"
        ],
        "hub_locations": [
            "boston",
            "cambridge",
            "san francisco",
            "bay area",
            "basel",
            "london",
            "oxford",
            "cambridge uk"
        ],
        "scoring_weights": {
            "title_match": 50,
            "company_funding": 20,
            "tech_usage": 25,
            "open_to_nams": 10,
            "hub_location": 20,
            "recent_publication": 60,
            "corresponding_author": 25
        }
    }
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=2)

# ===== IMPORT MODULES =====
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')

# Add src to Python path
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

try:
    # Import modules correctly
    from src.scraper.pubmed_scraper import PubMedScraper
    from src.scoring.score_calculator import LeadScorer
    from src.scoring.ranker import LeadRanker
    from src.utils.csv_handler import CSVHandler
    print("✅ All modules imported successfully")
except ImportError as e:
    st.error(f"❌ Import Error: {e}")
    st.error(f"Python path: {sys.path}")
    st.error(f"Looking for src folder at: {src_dir}")
    st.error("Check your folder structure and make sure 'src' folder exists")
    st.stop()

# ===== PAGE CONFIG =====
st.set_page_config(
    page_title="Lead Generation Dashboard",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== CUSTOM CSS =====
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #3B82F6;
        margin-top: 1rem;
    }
    .stButton > button {
        width: 100%;
    }
    .dataframe th {
        background-color: #1E3A8A;
        color: white;
        font-weight: bold;
    }
    .hot-score {
        color: #DC2626;
        font-weight: bold;
    }
    .warm-score {
        color: #EA580C;
        font-weight: bold;
    }
    .cold-score {
        color: #2563EB;
    }
    </style>
""", unsafe_allow_html=True)

# ===== DASHBOARD CLASS =====
class LeadDashboard:
    def __init__(self):
        try:
            self.scraper = PubMedScraper()
            self.scorer = LeadScorer()
            self.ranker = LeadRanker()
            self.csv_handler = CSVHandler()
            self.df = pd.DataFrame()
        except Exception as e:
            st.error(f"❌ Failed to initialize components: {e}")
            st.stop()
    
    def load_data(self):
        """Load existing data from CSV"""
        try:
            self.df = self.csv_handler.load_latest_data()
            if self.df.empty:
                st.info("📭 No data found. Click 'Scrape PubMed' to get real lead data.")
            else:
                st.success(f"📊 Loaded {len(self.df)} real leads from PubMed")
        except Exception as e:
            st.error(f"Error loading data: {e}")
            self.df = pd.DataFrame()
    
    def prepare_display_df(self, df):
        """Prepare DataFrame for display with proper column names"""
        if df.empty:
            return df
        
        display_df = df.copy()
        
        # Use the ranker's export_for_display method if available
        if hasattr(self.ranker, 'export_for_display'):
            display_df = self.ranker.export_for_display(display_df)
        else:
            # Manual column renaming
            rename_map = {
                'final_rank': 'Rank',
                'name': 'Name',
                'title': 'Title',
                'company': 'Company',
                'location': 'Location',
                'score': 'Score',
                'email': 'Email',
                'paper_title': 'Recent Paper'
            }
            
            # Rename only columns that exist
            for old_name, new_name in rename_map.items():
                if old_name in display_df.columns:
                    display_df = display_df.rename(columns={old_name: new_name})
        
        # Define display order
        display_order = ['Rank', 'Name', 'Title', 'Company', 'Location', 'Score', 'Email', 'Recent Paper']
        
        # Keep only columns that exist in the desired order
        existing_cols = [col for col in display_order if col in display_df.columns]
        other_cols = [col for col in display_df.columns if col not in existing_cols]
        
        return display_df[existing_cols + other_cols]
    
    def run(self):
        """Main dashboard function"""
        
        # ===== SIDEBAR =====
        with st.sidebar:
            st.image("https://cdn-icons-png.flaticon.com/512/2103/2103655.png", width=100)
            st.title("🔬 Lead Generator")
            st.markdown("---")
            
            st.subheader("🔍 Data Actions")
            
            # SCRAPE BUTTON
            if st.button("🔄 Scrape PubMed", type="primary", use_container_width=True):
                with st.spinner("🔄 Scraping real data from PubMed..."):
                    try:
                        # Scrape REAL data
                        new_df = self.scraper.find_authors_from_keywords()
                        
                        if new_df.empty:
                            st.error("""
                            ❌ No data scraped. Possible reasons:
                            1. PubMed API temporary issue
                            2. No papers match search terms
                            3. Network problem
                            """)
                            st.info("Check terminal for detailed logs")
                        else:
                            # Score and rank
                            scored_df = self.scorer.score_dataframe(new_df)
                            ranked_df = self.ranker.rank_leads(scored_df)
                            
                            # Save data
                            self.csv_handler.save_processed_data(ranked_df)
                            self.csv_handler.export_for_dashboard(ranked_df)
                            
                            # Update display
                            self.df = ranked_df
                            st.success(f"✅ Success! Found {len(new_df)} real leads")
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f"❌ Scraping failed: {str(e)}")
                        with st.expander("Technical Details"):
                            st.code(traceback.format_exc())
            
            st.markdown("---")
            
            # FILTERS SECTION
            st.subheader("🎯 Filters")
            
            # Always initialize filter variables
            score_range = (0, 100)
            selected_location = 'All'
            
            if not self.df.empty:
                # Score Filter
                if 'score' in self.df.columns:
                    min_score = int(self.df['score'].min())
                    max_score = int(self.df['score'].max())
                    
                    # Fix for equal values
                    if min_score >= max_score:
                        max_score = min_score + 10
                    
                    score_range = st.slider(
                        "Score Range",
                        min_score, max_score,
                        (min_score, max_score),
                        key="score_filter"
                    )
                else:
                    # Default range if no score column
                    score_range = st.slider(
                        "Score Range",
                        0, 100, (0, 100),
                        key="score_default"
                    )
                
                # Location Filter
                if 'location' in self.df.columns:
                    locations = ['All'] + sorted(self.df['location'].dropna().unique().tolist())
                    selected_location = st.selectbox(
                        "Location",
                        locations,
                        key="location_filter"
                    )
                else:
                    selected_location = 'All'
            else:
                # Default filters when no data
                score_range = st.slider(
                    "Score Range",
                    0, 100, (0, 100),
                    key="score_empty"
                )
                selected_location = 'All'
            
            st.markdown("---")
            
            # DOWNLOAD BUTTON
            if not self.df.empty:
                csv_data = self.df.to_csv(index=False)
                st.download_button(
                    "💾 Download All Data",
                    data=csv_data,
                    file_name=f"pubmed_leads_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        # ===== MAIN CONTENT =====
        st.markdown('<h1 class="main-header">🔬 3D In-Vitro Models Lead Generation</h1>', unsafe_allow_html=True)
        st.caption("Real data from PubMed - No sample data used")
        
        # Load data
        self.load_data()
        
        if self.df.empty:
            st.warning("""
            ## 📭 No Data Available
            
            To get started:
            1. Click **"Scrape PubMed"** in the sidebar
            2. Wait for real PubMed data to be fetched
            3. Leads will appear here automatically
            
            ⚠️ **Note:** This uses REAL PubMed API, not sample data.
            """)
            return
        
        # ===== APPLY FILTERS =====
        filtered_df = self.df.copy()
        
        try:
            # Score filter
            if 'score' in filtered_df.columns:
                filtered_df = filtered_df[
                    (filtered_df['score'] >= score_range[0]) & 
                    (filtered_df['score'] <= score_range[1])
                ]
            
            # Location filter
            if selected_location != 'All' and 'location' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['location'].str.contains(selected_location, na=False)]
        except Exception as e:
            st.error(f"Filter error: {e}")
            # Continue with unfiltered data
        
        # ===== METRICS =====
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Leads", len(filtered_df))
        
        with col2:
            if 'score' in filtered_df.columns:
                hot_leads = len(filtered_df[filtered_df['score'] >= 80])
                st.metric("Hot Leads (80+)", hot_leads)
            else:
                st.metric("Hot Leads", "N/A")
        
        with col3:
            if 'score' in filtered_df.columns and not filtered_df.empty:
                avg_score = filtered_df['score'].mean()
                st.metric("Average Score", f"{avg_score:.1f}")
            else:
                st.metric("Average Score", "N/A")
        
        with col4:
            if 'email' in filtered_df.columns:
                email_count = filtered_df['email'].notna().sum()
                st.metric("Emails Found", email_count)
            else:
                st.metric("Emails", "N/A")
        
        st.markdown("---")
        
        # ===== SEARCH =====
        st.markdown('<h2 class="sub-header">📋 Lead List</h2>', unsafe_allow_html=True)
        
        search_term = st.text_input("🔍 Search by name, company, or keyword", "")
        if search_term and not filtered_df.empty:
            try:
                search_mask = (
                    filtered_df['name'].astype(str).str.contains(search_term, case=False, na=False) |
                    filtered_df['company'].astype(str).str.contains(search_term, case=False, na=False) |
                    filtered_df['title'].astype(str).str.contains(search_term, case=False, na=False) |
                    filtered_df['paper_title'].astype(str).str.contains(search_term, case=False, na=False)
                )
                filtered_df = filtered_df[search_mask]
            except:
                pass  # If search fails, continue with current data
        
        # ===== DATA TABLE =====
        if not filtered_df.empty:
            # Prepare display DataFrame with proper column names
            display_df = self.prepare_display_df(filtered_df)
            
            # Display the table with proper formatting
            if 'Score' in display_df.columns:
                # Format the Score column with styling
                def format_score(val):
                    if pd.isna(val):
                        return ""
                    val = float(val)
                    if val >= 80:
                        return f'<span class="hot-score">{int(val)}</span>'
                    elif val >= 60:
                        return f'<span class="warm-score">{int(val)}</span>'
                    elif val >= 40:
                        return f'<span class="cold-score">{int(val)}</span>'
                    else:
                        return str(int(val))
                
                # Apply formatting
                display_df['Score'] = display_df['Score'].apply(format_score)
                
                # Display with HTML formatting
                st.markdown(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)
            else:
                # Display without score formatting
                st.dataframe(display_df, use_container_width=True, height=500)
            
            # Show record count
            st.caption(f"Showing {len(display_df)} of {len(self.df)} total leads")
        else:
            st.warning("No leads match your filters")
        
        # ===== EXPORT FILTERED DATA =====
        if not filtered_df.empty:
            csv_filtered = filtered_df.to_csv(index=False)
            st.download_button(
                "📥 Download Filtered Data",
                data=csv_filtered,
                file_name=f"filtered_leads_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # ===== ANALYTICS =====
        if not filtered_df.empty and len(filtered_df) > 1:
            st.markdown("---")
            st.markdown('<h2 class="sub-header">📊 Analytics</h2>', unsafe_allow_html=True)
            
            tab1, tab2, tab3 = st.tabs(["Score Distribution", "Top Locations", "Data Quality"])
            
            with tab1:
                if 'score' in filtered_df.columns:
                    fig = px.histogram(
                        filtered_df, x='score',
                        title='Lead Score Distribution',
                        nbins=20,
                        color_discrete_sequence=['#3B82F6']
                    )
                    fig.update_layout(
                        xaxis_title="Score",
                        yaxis_title="Number of Leads",
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                if 'location' in filtered_df.columns:
                    location_counts = filtered_df['location'].value_counts().head(15)
                    if len(location_counts) > 0:
                        fig = px.bar(
                            x=location_counts.values,
                            y=location_counts.index,
                            orientation='h',
                            title='Top Locations',
                            color=location_counts.values,
                            color_continuous_scale='Viridis'
                        )
                        fig.update_layout(
                            xaxis_title="Number of Leads",
                            yaxis_title="Location",
                            showlegend=False
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            with tab3:
                col1, col2 = st.columns(2)
                with col1:
                    if 'email' in filtered_df.columns:
                        email_pct = (filtered_df['email'].notna().sum() / len(filtered_df)) * 100
                        st.metric("Email Coverage", f"{email_pct:.1f}%")
                    
                    if 'is_corresponding_author' in filtered_df.columns:
                        ca_count = filtered_df['is_corresponding_author'].sum()
                        st.metric("Corresponding Authors", ca_count)
                
                with col2:
                    if 'paper_date' in filtered_df.columns:
                        recent_papers = 0
                        try:
                            current_year = datetime.now().year
                            for date in filtered_df['paper_date']:
                                if date and str(date)[:4].isdigit():
                                    if int(str(date)[:4]) >= current_year - 2:
                                        recent_papers += 1
                        except:
                            pass
                        st.metric("Recent Papers (2 yrs)", recent_papers)
        
        # ===== DEBUG INFO =====
        with st.expander("🔧 Technical Details"):
            st.write(f"**Total Records:** {len(self.df)}")
            st.write(f"**Filtered Records:** {len(filtered_df)}")
            
            if not self.df.empty:
                st.write("**Raw Columns:**", list(self.df.columns))
                
                if 'score' in self.df.columns:
                    st.write("**Score Statistics:**")
                    st.write(f"- Minimum: {self.df['score'].min()}")
                    st.write(f"- Maximum: {self.df['score'].max()}")
                    st.write(f"- Average: {self.df['score'].mean():.1f}")
                    st.write(f"- Std Dev: {self.df['score'].std():.1f}")
                
                st.write("**Data Source:** PubMed API (Real Data)")
                st.write(f"**Last Scrape:** Check data/processed/leads.csv timestamp")

# ===== RUN APP =====
if __name__ == "__main__":
    try:
        dashboard = LeadDashboard()
        dashboard.run()
    except Exception as e:
        st.error(f"🚨 Fatal Error: {e}")
        st.info("""
        ## 🛠️ Troubleshooting:
        
        1. **Check internet connection** - PubMed API requires internet
        2. **Verify folder structure:**
           ```
           project/
           ├── app.py
           ├── config/keywords.json
           ├── src/
           │   ├── scraper/pubmed_scraper.py
           │   ├── scoring/score_calculator.py
           │   ├── scoring/ranker.py
           │   ├── utils/data_cleaner.py
           │   └── utils/csv_handler.py
           └── data/
               ├── processed/
               └── raw/
           ```
        3. **Check terminal for detailed errors:**
           ```bash
           streamlit run app.py
           ```
        """)
        with st.expander("Full Error Traceback"):
            st.code(traceback.format_exc())