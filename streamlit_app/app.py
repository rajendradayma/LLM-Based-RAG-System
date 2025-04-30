import streamlit as st
import requests

st.title("LLM-based RAG Search")

# Input for user query
query = st.text_input("Enter your query:")

if st.button("Search") and query:
    with st.spinner("Searching for answers..."):
        try:
            # Make a POST request to the Flask API
            flask_url = "http://localhost:5001/query"
            print(f"Accessing {flask_url} with query: {query}")

            response = requests.post(
                flask_url,
                json={"query": query},
                timeout=30  # 30 second timeout
            )

            print(f"Received status code: {response.status_code}")

            if response.status_code == 200:
                # Display the generated answer and sources
                result = response.json()
                st.subheader("Answer:")
                st.write(result.get('answer', "No answer generated."))

                sources = result.get('sources', [])
                if sources:
                    st.subheader("Sources:")
                    for url in sources:
                        st.write(f"- {url}")
            else:
                error_msg = response.json().get('error', f"HTTP Error {response.status_code}")
                st.error(f"API Error: {error_msg}")

        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
            print(f"Request failed: {str(e)}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
            print(f"Error: {str(e)}")

# Add some instructions
st.sidebar.markdown("""
### How to use this RAG system:
1. Enter your question in the search box
2. Click the Search button
3. View the generated answer
4. Check the sources for reference

Note: First make sure the Flask backend is running on port 5001.
""")
