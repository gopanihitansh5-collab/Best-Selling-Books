import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="BookMetrics Pro",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# CUSTOM CSS FOR SAAS FEEL
# -------------------------
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h1 {
        color: #1f2937;
        font-weight: 700;
    }
    h2, h3 {
        color: #374151;
    }
    .reportview-container .markdown-text-container {
        font-family: 'Inter', sans-serif;
    }
    div[data-testid="stSidebarNav"] {
        background-color: #1f2937;
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------------
# LOAD DATA FUNCTION
# -------------------------
@st.cache_data
def load_data():
    """Load and clean the bestselling books dataset"""
    try:
        df = pd.read_csv("best sellin books 2023.csv", encoding="latin1")
    except FileNotFoundError:
        st.error("⚠️ Dataset file not found. Please upload 'best sellin books 2023.csv'")
        return None
    
    # Data Cleaning Pipeline
    # 1. Clean Rating - Extract numeric value
    df["Rating"] = df["Rating"].str.extract(r"(\d+\.\d+)").astype(float)
    
    # 2. Clean Price - Remove $ and convert to float
    df["price"] = df["price"].replace('[\$,]', '', regex=True).astype(float)
    
    # 3. Clean Rank - Remove # symbol
    df["Rank"] = df["id"].str.replace("#", "").astype(int)
    
    # 4. Convert Publishing Date
    df["Publishing date"] = pd.to_datetime(df["Publishing date"], errors="coerce")
    df["Year"] = df["Publishing date"].dt.year
    df["Month"] = df["Publishing date"].dt.month
    
    # 5. Create calculated fields
    df["Estimated Revenue"] = df["price"] * df["reviews count"]
    df["Popularity Score"] = df["Rating"] * np.log1p(df["reviews count"])
    
    # 6. Handle missing values
    df["Reading age"] = df["Reading age"].fillna("Not Specified")
    
    return df

# -------------------------
# LOAD DATA
# -------------------------
df = load_data()

if df is None:
    st.stop()

# -------------------------
# SIDEBAR - FILTERS & BRANDING
# -------------------------
with st.sidebar:
    st.image("https://via.placeholder.com/250x80/1f2937/ffffff?text=BookMetrics+Pro", use_container_width=True)
    st.markdown("### 📊 Analytics Dashboard")
    st.markdown("---")
    
    st.markdown("#### 🔍 Filters")
    
    # Genre Filter
    genre_options = ["All Genres"] + sorted(df["Genre"].unique().tolist())
    genre_filter = st.multiselect(
        "Genre",
        options=genre_options,
        default=["All Genres"]
    )
    
    # Apply genre filter logic
    if "All Genres" in genre_filter or len(genre_filter) == 0:
        genre_mask = df["Genre"].notna()
    else:
        genre_mask = df["Genre"].isin(genre_filter)
    
    # Author Filter
    author_options = ["All Authors"] + sorted(df["Author"].unique().tolist())
    author_filter = st.multiselect(
        "Author",
        options=author_options,
        default=["All Authors"]
    )
    
    # Apply author filter logic
    if "All Authors" in author_filter or len(author_filter) == 0:
        author_mask = df["Author"].notna()
    else:
        author_mask = df["Author"].isin(author_filter)
    
    # Price Range
    price_range = st.slider(
        "Price Range ($)",
        float(df["price"].min()),
        float(df["price"].max()),
        (float(df["price"].min()), float(df["price"].max())),
        step=1.0
    )
    
    # Rating Filter
    rating_filter = st.slider(
        "Minimum Rating",
        0.0, 5.0, 0.0, 0.1
    )
    
    # Format Filter
    format_options = ["All Formats"] + df["form"].unique().tolist()
    format_filter = st.selectbox("Format", format_options)
    
    # Year Filter
    year_options = ["All Years"] + sorted([y for y in df["Year"].dropna().unique() if not pd.isna(y)], reverse=True)
    year_filter = st.selectbox("Publication Year", year_options)
    
    st.markdown("---")
    st.markdown("#### 📈 Quick Stats")
    st.metric("Total Books in DB", len(df))
    st.metric("Genres", df["Genre"].nunique())
    st.metric("Authors", df["Author"].nunique())

# -------------------------
# APPLY FILTERS
# -------------------------
filtered_df = df[genre_mask & author_mask]

# Apply other filters
filtered_df = filtered_df[
    (filtered_df["price"].between(price_range[0], price_range[1])) &
    (filtered_df["Rating"] >= rating_filter)
]

if format_filter != "All Formats":
    filtered_df = filtered_df[filtered_df["form"] == format_filter]

if year_filter != "All Years":
    filtered_df = filtered_df[filtered_df["Year"] == year_filter]

# -------------------------
# HEADER
# -------------------------
st.title("📚 BookMetrics Pro – Market Intelligence Dashboard")
st.markdown("**Premium Analytics Platform for Publishers, Authors & Investors**")
st.markdown(f"*Analysis based on {len(filtered_df)} books matching your filters*")

# -------------------------
# KPI SECTION
# -------------------------
st.markdown("### 📊 Key Performance Indicators")

col1, col2, col3, col4, col5 = st.columns(5)

total_books = filtered_df.shape[0]
avg_rating = round(filtered_df["Rating"].mean(), 2)
total_reviews = int(filtered_df["reviews count"].sum())
avg_price = round(filtered_df["price"].mean(), 2)
total_revenue = filtered_df["Estimated Revenue"].sum()

with col1:
    st.metric("📦 Total Books", f"{total_books:,}")

with col2:
    st.metric("⭐ Avg Rating", f"{avg_rating}/5.0")

with col3:
    st.metric("🗣️ Total Reviews", f"{total_reviews:,}")

with col4:
    st.metric("💰 Avg Price", f"${avg_price}")

with col5:
    st.metric("💵 Est. Revenue", f"${total_revenue/1e6:.1f}M")

st.markdown("---")

# -------------------------
# ROW 1: TOP PERFORMERS
# -------------------------
st.markdown("### 🏆 Top Performers")

tab1, tab2, tab3 = st.tabs(["📈 By Reviews", "⭐ By Rating", "💰 By Revenue"])

with tab1:
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        top_reviews = filtered_df.nlargest(10, "reviews count")
        
        fig1 = px.bar(
            top_reviews,
            y="Book name",
            x="reviews count",
            orientation="h",
            title="Top 10 Most Reviewed Books",
            color="Rating",
            color_continuous_scale="viridis",
            hover_data=["Author", "price", "Genre"]
        )
        fig1.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig1, use_container_width=True)
    
    with col_b:
        st.markdown("#### 📋 Details")
        for idx, row in top_reviews.head(5).iterrows():
            with st.container():
                st.markdown(f"**{row['Book name'][:40]}...**")
                st.caption(f"By {row['Author']}")
                st.caption(f"⭐ {row['Rating']} | 💬 {row['reviews count']:,} reviews")
                st.markdown("---")

with tab2:
    top_rated = filtered_df.nlargest(10, "Rating")
    
    fig2 = px.scatter(
        top_rated,
        x="reviews count",
        y="Rating",
        size="Estimated Revenue",
        color="Genre",
        hover_data=["Book name", "Author", "price"],
        title="Highest Rated Books (size = revenue)",
        size_max=50
    )
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    top_revenue = filtered_df.nlargest(10, "Estimated Revenue")
    
    fig3 = px.bar(
        top_revenue,
        y="Book name",
        x="Estimated Revenue",
        orientation="h",
        title="Top 10 Revenue Generators",
        color="price",
        color_continuous_scale="reds",
        hover_data=["Author", "reviews count", "Rating"]
    )
    fig3.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# -------------------------
# ROW 2: MARKET ANALYSIS
# -------------------------
st.markdown("### 📊 Market Analysis")

col_c, col_d = st.columns(2)

with col_c:
    st.markdown("#### Genre Performance")
    
    genre_stats = filtered_df.groupby("Genre").agg({
        "Rating": "mean",
        "reviews count": "sum",
        "Estimated Revenue": "sum",
        "Book name": "count"
    }).reset_index()
    genre_stats.columns = ["Genre", "Avg Rating", "Total Reviews", "Est Revenue", "Book Count"]
    
    fig4 = px.bar(
        genre_stats.sort_values("Total Reviews", ascending=False),
        x="Genre",
        y="Total Reviews",
        title="Total Reviews by Genre",
        color="Avg Rating",
        color_continuous_scale="thermal"
    )
    fig4.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig4, use_container_width=True)

with col_d:
    st.markdown("#### Revenue Distribution by Genre")
    
    fig5 = px.pie(
        genre_stats,
        values="Est Revenue",
        names="Genre",
        title="Market Share by Estimated Revenue",
        hole=0.4
    )
    st.plotly_chart(fig5, use_container_width=True)

# -------------------------
# ROW 3: PRICING & FORMAT ANALYSIS
# -------------------------
col_e, col_f = st.columns(2)

with col_e:
    st.markdown("#### 💰 Price Distribution")
    
    fig6 = px.histogram(
        filtered_df,
        x="price",
        nbins=30,
        title="Price Distribution of Bestsellers",
        color_discrete_sequence=["#3b82f6"]
    )
    fig6.add_vline(x=avg_price, line_dash="dash", line_color="red", 
                   annotation_text=f"Avg: ${avg_price}")
    st.plotly_chart(fig6, use_container_width=True)

with col_f:
    st.markdown("#### 📖 Format Preference")
    
    format_dist = filtered_df["form"].value_counts().reset_index()
    format_dist.columns = ["Format", "Count"]
    
    fig7 = px.pie(
        format_dist,
        values="Count",
        names="Format",
        title="Market Format Distribution"
    )
    st.plotly_chart(fig7, use_container_width=True)

st.markdown("---")

# -------------------------
# ROW 4: CORRELATION ANALYSIS
# -------------------------
st.markdown("### 🔬 Advanced Analytics")

col_g, col_h = st.columns(2)

with col_g:
    st.markdown("#### Print Length vs Rating")
    
    fig8 = px.scatter(
        filtered_df,
        x="Print Length",
        y="Rating",
        size="reviews count",
        color="Genre",
        hover_data=["Book name", "Author", "price"],
        title="Do Longer Books Get Better Ratings?",
        trendline="ols"
    )
    st.plotly_chart(fig8, use_container_width=True)

with col_h:
    st.markdown("#### Price vs Reviews")
    
    fig9 = px.scatter(
        filtered_df,
        x="price",
        y="reviews count",
        color="Rating",
        size="Print Length",
        hover_data=["Book name", "Author"],
        title="Are Expensive Books More Popular?",
        color_continuous_scale="viridis"
    )
    st.plotly_chart(fig9, use_container_width=True)

st.markdown("---")

# -------------------------
# ROW 5: AUTHOR INTELLIGENCE
# -------------------------
st.markdown("### 👑 Author Dominance")

col_i, col_j = st.columns([3, 2])

with col_i:
    author_stats = filtered_df.groupby("Author").agg({
        "reviews count": "sum",
        "Rating": "mean",
        "Estimated Revenue": "sum",
        "Book name": "count"
    }).reset_index()
    author_stats.columns = ["Author", "Total Reviews", "Avg Rating", "Est Revenue", "Book Count"]
    
    top_authors = author_stats.nlargest(15, "Total Reviews")
    
    fig10 = px.bar(
        top_authors,
        y="Author",
        x="Total Reviews",
        orientation="h",
        title="Top 15 Authors by Total Reviews",
        color="Avg Rating",
        color_continuous_scale="greens",
        hover_data=["Book Count", "Est Revenue"]
    )
    fig10.update_layout(height=500, yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig10, use_container_width=True)

with col_j:
    st.markdown("#### 🌟 Top Author Metrics")
    
    for idx, row in top_authors.head(8).iterrows():
        with st.expander(f"**{row['Author']}**"):
            st.metric("Books", int(row['Book Count']))
            st.metric("Avg Rating", f"{row['Avg Rating']:.2f}")
            st.metric("Total Reviews", f"{int(row['Total Reviews']):,}")
            st.metric("Est. Revenue", f"${row['Est Revenue']/1e6:.2f}M")

st.markdown("---")

# -------------------------
# ROW 6: PUBLISHING TRENDS
# -------------------------
st.markdown("### 📅 Publishing Trends")

# Filter out NaN years
trend_df = filtered_df[filtered_df["Year"].notna()].copy()

if not trend_df.empty:
    col_k, col_l = st.columns(2)
    
    with col_k:
        yearly_trend = trend_df.groupby("Year").agg({
            "Book name": "count",
            "Rating": "mean",
            "reviews count": "sum"
        }).reset_index()
        yearly_trend.columns = ["Year", "Book Count", "Avg Rating", "Total Reviews"]
        
        fig11 = px.line(
            yearly_trend,
            x="Year",
            y="Book Count",
            title="Books Published Over Time",
            markers=True
        )
        st.plotly_chart(fig11, use_container_width=True)
    
    with col_l:
        fig12 = px.bar(
            yearly_trend,
            x="Year",
            y="Total Reviews",
            title="Review Volume by Publication Year",
            color="Avg Rating",
            color_continuous_scale="blues"
        )
        st.plotly_chart(fig12, use_container_width=True)
else:
    st.info("No publication date data available for filtered results")

st.markdown("---")

# -------------------------
# ROW 7: DATA TABLE
# -------------------------
st.markdown("### 📋 Detailed Data Explorer")

# Prepare display dataframe
display_df = filtered_df[[
    "Rank", "Book name", "Author", "Genre", "Rating", 
    "reviews count", "price", "form", "Print Length", 
    "Publishing date", "Estimated Revenue", "Popularity Score"
]].sort_values("Rank")

# Format columns
display_df["price"] = display_df["price"].apply(lambda x: f"${x:.2f}")
display_df["Estimated Revenue"] = display_df["Estimated Revenue"].apply(lambda x: f"${x:,.0f}")
display_df["Popularity Score"] = display_df["Popularity Score"].apply(lambda x: f"{x:.1f}")
display_df["reviews count"] = display_df["reviews count"].apply(lambda x: f"{x:,}")

st.dataframe(
    display_df,
    use_container_width=True,
    height=400,
    hide_index=True
)

# Download button
csv = filtered_df.to_csv(index=False)
st.download_button(
    label="📥 Download Filtered Data as CSV",
    data=csv,
    file_name=f"filtered_books_{datetime.now().strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

st.markdown("---")

# -------------------------
# FOOTER
# -------------------------
st.markdown("""
    <div style='text-align: center; color: #6b7280; padding: 20px;'>
        <p>© 2026 BookMetrics Pro | Powered by Streamlit & Plotly</p>
        <p>📊 Professional Market Intelligence for the Publishing Industry</p>
    </div>
    """, unsafe_allow_html=True)
