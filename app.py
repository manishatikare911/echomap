import pandas as pd
import re
import streamlit as st

st.set_page_config(page_title="Customer Feedback Explorer", layout="wide")
st.title("📄 Customer Feedback Keyword.")

# 🚀 Upload CSV
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

# ⚡ Load and process data
@st.cache_data
def load_and_process(file):
    try:
        df = pd.read_csv(file)
        if df.empty:
            st.error("The uploaded CSV file is empty.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
        return pd.DataFrame()

    # Extract structured fields
    def extract_sections(text):
        issue = re.search(r"<b>Customer Issue:</b>(.*?)<b>Agent's Actions:</b>", text, re.DOTALL)
        actions = re.search(r"<b>Agent's Actions:</b>(.*?)<b>Customer's Anxiety:</b>", text, re.DOTALL)
        anxiety = re.search(r"<b>Customer's Anxiety:</b>(.*?)<b>Important Keywords:</b>", text, re.DOTALL)
        keywords = re.search(r"<b>Important Keywords:</b>(.*)", text, re.DOTALL)
        return pd.Series({
            "Customer Issue": issue.group(1).strip() if issue else "",
            "Agent's Actions": actions.group(1).strip() if actions else "",
            "Customer's Anxiety": anxiety.group(1).strip() if anxiety else "",
            "Important Keywords": keywords.group(1).strip() if keywords else ""
        })

    # Detect feedback column
    text_column = next((col for col in df.columns if 'thread_text' in col.lower()), None)
    if not text_column:
        st.error("No column named 'thread_text' found.")
        return pd.DataFrame()

    df_cleaned = pd.DataFrame(df[text_column].apply(extract_sections))

    # Keyword list
    df_cleaned['Keyword List'] = df_cleaned['Important Keywords'].apply(
        lambda x: [kw.strip() for kw in str(x).split('_') if kw.strip()]
    )

    # Add extra columns
    for col in ['ASP_slab', 'analytic_business_unit', 'vip_flag', 'sub_sub_issue_type']:
        df_cleaned[col] = df[col] if col in df.columns else ""

    return df_cleaned

# 🧠 Display
if uploaded_file:
    df_cleaned = load_and_process(uploaded_file)

    if not df_cleaned.empty:
        # Keyword frequency
        keyword_freq = {}
        for kws in df_cleaned['Keyword List']:
            for kw in kws:
                keyword_freq[kw] = keyword_freq.get(kw, 0) + 1
        sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
        keyword_options = [kw for kw, _ in sorted_keywords]

        # 😟 Anxiety Level Counts
        st.subheader("😟 Anxiety Level Counts")
        anxiety_counts = df_cleaned["Customer's Anxiety"].dropna()
        anxiety_counts = anxiety_counts[anxiety_counts.str.strip() != ""].value_counts()
        anxiety_df = pd.DataFrame({
            "Anxiety Level": anxiety_counts.index,
            "Count": anxiety_counts.values
        })
        total_row = pd.DataFrame([{
            "Anxiety Level": "Total",
            "Count": anxiety_df["Count"].sum()
        }])
        anxiety_df_with_total = pd.concat([anxiety_df, total_row], ignore_index=True)
        st.dataframe(anxiety_df_with_total)

        # 📊 Attribute Distribution
        st.subheader("📊 Attribute Distribution by Column")
        col1, col2 = st.columns(2)

        with col1:
            asp_counts = df_cleaned['ASP_slab'].fillna("").astype(str).value_counts().reset_index()
            asp_counts.columns = ['ASP_slab', 'Count']
            st.markdown("**ASP Slab Distribution**")
            st.dataframe(asp_counts)

            vip_counts = df_cleaned['vip_flag'].fillna("").astype(str).value_counts().reset_index()
            vip_counts.columns = ['VIP Flag', 'Count']
            st.markdown("**VIP Flag Distribution**")
            st.dataframe(vip_counts)

        with col2:
            abu_counts = df_cleaned['analytic_business_unit'].fillna("").astype(str).value_counts().reset_index()
            abu_counts.columns = ['Analytic Business Unit', 'Count']
            st.markdown("**Analytic Business Unit Distribution**")
            st.dataframe(abu_counts)

            sub_issue_counts = df_cleaned['sub_sub_issue_type'].fillna("").astype(str).value_counts().reset_index()
            sub_issue_counts.columns = ['Sub-sub Issue Type', 'Count']
            st.markdown("**Sub-sub Issue Type Distribution**")
            st.dataframe(sub_issue_counts)

        # 📊 Anxiety Chart
        st.subheader("📊 Anxiety Level Distribution")
        if not anxiety_counts.empty:
            st.bar_chart(anxiety_counts)

        # 🔑 Top N Keywords
        st.subheader("🔑 Top N Important Keywords")
        top_keywords_df = pd.DataFrame(sorted_keywords, columns=["Keyword", "Frequency"])

        # Limit step options to a maximum of 200
        max_keywords = min(len(top_keywords_df), 200)
        step_options = [i for i in range(10, max_keywords + 1, 10)]

        top_n = st.selectbox("Select how many top keywords to display:", step_options)
        st.dataframe(top_keywords_df.head(top_n))

        # 🎯 Filter by Keyword
        st.subheader("🎯 Filter by Top Keyword")
        selected_keyword = st.selectbox("Select a keyword to filter feedback", keyword_options)
        filtered_df_dropdown = df_cleaned[df_cleaned['Keyword List'].apply(lambda kws: selected_keyword in kws)]
        st.write(f"Showing feedbacks containing keyword: **{selected_keyword}**")
        st.dataframe(filtered_df_dropdown)

        # 🔍 Search by Keywords
        st.subheader("🔍 Search Any or Multiple Important Keywords")
        search_input = st.text_input("Enter keywords separated by commas:")
        if search_input:
            search_keywords = [kw.strip().lower() for kw in search_input.split(',') if kw.strip()]
            filtered_df_text = df_cleaned[df_cleaned['Keyword List'].apply(
                lambda kws: any(kw in [k.lower() for k in kws] for kw in search_keywords)
            )]
            st.write(f"Showing feedbacks containing: **{', '.join(search_keywords)}**")
            st.dataframe(filtered_df_text)

        # 🧾 Search Customer Issue
        st.subheader("🧾 Search Customer Issue Text")
        issue_input = st.text_input("Search in Customer Issue:")
        if issue_input:
            filtered_issue_df = df_cleaned[df_cleaned['Customer Issue'].str.contains(issue_input, case=False, na=False)]
            st.dataframe(filtered_issue_df)

        # 🛠️ Search Agent's Actions
        st.subheader("🛠️ Search Agent's Actions Text")
        action_input = st.text_input("Search in Agent's Actions:")
        if action_input:
            filtered_action_df = df_cleaned[df_cleaned["Agent's Actions"].str.contains(action_input, case=False, na=False)]
            st.dataframe(filtered_action_df)

        # 📦 All Data
        st.subheader("📦 All Feedback Data")
        st.dataframe(df_cleaned)

        # 📬 Contact Info
        st.markdown("---")
        st.markdown("**Contact: Jayanth G**  \n📧 Email: [jayanth.g@flipkart.com](mailto:jayanth.g@flipkart.com)")
        st.markdown("**Contact: Manisha Tikare**  \n📧 Email: [hgs.46020@partner.flipkart.com](mailto:hgs.46020@partner.flipkart.com)")
