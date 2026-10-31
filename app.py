import datetime
import streamlit as st

# Title of our website
st.title("💊 My Magic Medicine Tracker")
import streamlit as st 
import datetime
# 1. Type the medicine info
name = st.text_input("What is the medicine name?")
stock = st.number_input("How many pills are left?", min_value=0, value=10)
expiry_date = st.date_input("When does it expire?")

# 2. Save button
if st.button("Save Medicine"):
  st.success(f"Yay! Saved {name} into our medicine box!")

# 3. The Robot Guard (Stock and Expiry Alerts)
st.subheader("🚨 Robot Guard Alerts:")

# Check if stock is running low
if stock <= 3 and stock > 0:
  st.warning(f"⚠️ Oh no! {name} is running low! Only {stock} pills left!")
elif stock == 0:
  st.error(f"❌ Stop! {name} is completely empty! Time to buy more!")

# Check if medicine is expired
today = datetime.date.today()
if expiry_date < today:
  st.error(f"❌ Yikes! {name} is expired! Do not take it, throw it away!")
else:
  st.info(f"✅ {name} is safe to use!")