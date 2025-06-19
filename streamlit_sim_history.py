def show_sim_history(user_email):
    st.title("🕓 My Simulation History")

    try:
        response = supabase.table("simulations").select("*").eq("email", user_email).order("timestamp", desc=True).execute()

        if not response.data:
            st.info("No simulations found.")
            return

        for sim in response.data:
            st.markdown("---")
            st.write(f"**Date**: {sim.get('timestamp', 'Unknown')}")
            st.write("**Teams**:")
            teams = sim.get("teams", [])
            for t in teams:
                st.write(f"- {t}")

            if "standings" in sim:
                df = pd.DataFrame(sim["standings"])
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("No standings data available.")

    except Exception as e:
        st.error(f"Failed to load history: {e}")
