# =============================================================
# 🌍 AI-Based Travel Planner
# Developed using Python + Streamlit + MySQL
# By: Sahil Naykodi
# =============================================================

import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime

# =============================================================
# DATABASE CONNECTION
# =============================================================
def create_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Sahil@8511"  # 🔹 change this to your MySQL password
    )

# =============================================================
# DATABASE INITIALIZATION
# =============================================================
def init_db():
    conn = create_connection()
    cursor = conn.cursor()

    # Create database
    cursor.execute("CREATE DATABASE IF NOT EXISTS travel_planner_db")
    cursor.execute("USE travel_planner_db")

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            loc_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            type VARCHAR(50),         -- Attraction / Restaurant / Hotel
            zone VARCHAR(50),         -- City area
            opening_hour TIME,
            closing_hour TIME,
            rating FLOAT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itineraries (
            itin_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            loc_id INT,
            day INT,
            sequence INT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (loc_id) REFERENCES locations(loc_id)
        )
    """)

    conn.commit()
    conn.close()

# =============================================================
# MAIN APP
# =============================================================
def main():
    st.set_page_config(page_title="AI Travel Planner", page_icon="✈️", layout="wide")
    st.title("✈️ AI-Based Travel Planner")
    init_db()

    tab1, tab2, tab3 = st.tabs(["🏢 Admin Panel", "🧳 User Planner", "📋 View Itinerary"])

    # ---------------- Admin Panel ----------------
    with tab1:
        st.header("🏢 Add Location (Attraction / Restaurant / Hotel)")
        name = st.text_input("Name of Place")
        type_ = st.selectbox("Type", ["Attraction", "Restaurant", "Hotel"])
        zone = st.text_input("Zone/Area in City")
        opening = st.time_input("Opening Hour")
        closing = st.time_input("Closing Hour")
        rating = st.number_input("Rating (1-5)", min_value=1.0, max_value=5.0, step=0.1)

        if st.button("Add Location"):
            if name and type_ and zone:
                conn = create_connection()
                cursor = conn.cursor()
                cursor.execute("USE travel_planner_db")
                cursor.execute("""
                    INSERT INTO locations (name, type, zone, opening_hour, closing_hour, rating)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (name, type_, zone, opening, closing, rating))
                conn.commit()
                conn.close()
                st.success(f"✅ {name} added successfully!")
            else:
                st.warning("⚠️ Fill all required fields")

    # ---------------- User Planner ----------------
    with tab2:
        st.header("🧳 Generate Itinerary")
        user_name = st.text_input("Your Name")
        user_email = st.text_input("Your Email")
        city_days = st.number_input("Number of Days", min_value=1, max_value=14, step=1)
        preferences = st.multiselect("Preferred Types", ["Attraction", "Restaurant", "Hotel"])

        if st.button("Generate Itinerary"):
            if not (user_name and user_email and preferences):
                st.warning("⚠️ Fill all fields and select preferences")
            else:
                conn = create_connection()
                cursor = conn.cursor()
                cursor.execute("USE travel_planner_db")

                # Add user
                cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)", (user_name, user_email))
                user_id = cursor.lastrowid

                # Get locations based on preferences, sorted by rating
                cursor.execute(f"""
                    SELECT loc_id FROM locations
                    WHERE type IN ({','.join(['%s']*len(preferences))})
                    ORDER BY rating DESC
                """, tuple(preferences))
                loc_ids = [row[0] for row in cursor.fetchall()]

                # Simple distribution across days
                itinerary = []
                for i, loc_id in enumerate(loc_ids):
                    day = (i % city_days) + 1
                    sequence = (i // city_days) + 1
                    itinerary.append((user_id, loc_id, day, sequence))

                # Insert into itineraries
                cursor.executemany("""
                    INSERT INTO itineraries (user_id, loc_id, day, sequence)
                    VALUES (%s, %s, %s, %s)
                """, itinerary)

                conn.commit()
                conn.close()
                st.success("✅ Itinerary generated successfully!")

    # ---------------- View Itinerary ----------------
    with tab3:
        st.header("📋 View Itineraries")
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("USE travel_planner_db")

        cursor.execute("""
            SELECT u.name, u.email, l.name, l.type, l.zone, i.day, i.sequence
            FROM itineraries i
            JOIN users u ON i.user_id = u.user_id
            JOIN locations l ON i.loc_id = l.loc_id
            ORDER BY u.user_id, i.day, i.sequence
        """)
        rows = cursor.fetchall()
        conn.close()

        if rows:
            df = pd.DataFrame(rows, columns=["User Name","Email","Place","Type","Zone","Day","Sequence"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("ℹ️ No itineraries yet. Generate one in User Planner tab.")

# Run the app
if __name__ == "__main__":
    main()
