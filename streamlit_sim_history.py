import streamlit as st
import pandas as pd
from playoff import display_bracket_table_v4

def show_sim_history(supabase):
    user_email = st.session_state["user"].email
    sims = (
        supabase
        .table("simulations")
        .select("*")
        .eq("email", user_email)
        .order("timestamp", desc=True)
        .execute()
        .data
    )

    if not sims:
        st.info("You haven’t saved any simulations yet.")
        return

    for sim in sims:
        with st.expander(f"{sim['name']} — {sim['timestamp'][:19].replace('T', ' ')}"):
            # … your existing code to display teams & inline standings/playoffs …

            # Only show Delete button here:
            col1, col2 = st.columns([1,1])
            with col1:
                del_key = f"del_{sim['name']}_{sim['timestamp']}"
                if st.button("🗑 Delete", key=del_key):
                    supabase.table("simulations") \
                            .delete() \
                            .eq("email", user_email) \
                            .eq("name", sim["name"]) \
                            .execute()
                    st.success("Deleted.")
                    st.rerun()

            # Show results inline if available
            if "standings" in sim and sim["standings"]:
                st.markdown("### 🏒 Standings")
                df = pd.DataFrame(sim["standings"])
                view_mode = st.selectbox(
                    f"View Mode for '{sim['name']}'",
                    ["By Division", "By Conference", "Entire League", "Playoffs"],
                    key=f"view_mode_{sim['name']}"
                )

                if view_mode == "By Division":
                    for div in df["Division"].unique():
                        st.write(f"#### {div}")
                        div_df = df[df["Division"] == div].sort_values(by=["PTS", "Win%"], ascending=[False, False]).reset_index(drop=True)
                        div_df.insert(0, "#", range(1, len(div_df) + 1))
                        st.dataframe(div_df[["#", "Team", "GP", "W", "L", "OTL", "PTS", "Win%"]], use_container_width=True, hide_index=True)


                elif view_mode == "By Conference":
                    for conf in df["Conference"].unique():
                        st.write(f"#### {conf}")
                        conf_df = df[df["Conference"] == conf].sort_values(by=["PTS", "Win%"], ascending=[False, False]).reset_index(drop=True)
                        conf_df.insert(0, "#", range(1, len(conf_df) + 1))
                        st.dataframe(conf_df[["#", "Team", "GP", "W", "L", "OTL", "PTS", "Win%"]], use_container_width=True, hide_index=True)


                elif view_mode == "Entire League":
                    league_df = df.sort_values(by=["PTS", "Win%"], ascending=[False, False]).reset_index(drop=True)
                    league_df.insert(0, "#", range(1, len(league_df) + 1))
                    st.dataframe(league_df[["#", "Team", "GP", "W", "L", "OTL", "PTS", "Win%"]], use_container_width=True, hide_index=True)


                else:  # Playoffs
                    from playoff import display_bracket_table_v4
                    st.subheader("🏆 Playoff Bracket")
                    display_bracket_table_v4(sim["playoffs"])
