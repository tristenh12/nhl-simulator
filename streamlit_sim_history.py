import streamlit as st

def show_sim_history(supabase):
    user_email = st.session_state["user"].email
    sims = supabase.table("simulations").select("*").eq("email", user_email).order("timestamp", desc=True).execute().data

    if not sims:
        st.info("You haven’t saved any simulations yet.")
        return

    for sim in sims:
        with st.expander(f"{sim['name']} — {sim['timestamp'][:19].replace('T', ' ')}"):
            st.write("**Teams:**")
            st.write(sim["teams"])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Load", key=f"load_{sim['name']}_{sim['timestamp']}"):
                    st.session_state["team_slots"] = [
                        {"team": t.split(" (")[0], "season": int(t.split(" (")[1][:-1])}
                        for t in sim["teams"]
                    ]
                    st.session_state["load_trigger"] = True
                    st.success("Loaded into Full Sim tab.")

            with col2:
                if st.button("Delete", key=f"del_{sim['name']}_{sim['timestamp']}"):
                    supabase.table("simulations").delete().eq("email", user_email).eq("name", sim["name"]).execute()
                    st.success("Deleted.")
                    st.rerun()
