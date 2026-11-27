import requests
import pandas as pd
import streamlit as st
from rag_assistant import render_rag_assistant
# API connection
API = os.getenv("API_URL", "http://localhost:8000")

STOP_REASONS = {
    "E101": "Power failure",
    "E102": "Motor overheating",
    "E103": "Material shortage",
    "E104": "Emergency stop"
}

st.set_page_config(
    page_title="Industrial IoT Analytics",
    page_icon="≡ƒÅ¡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
<style>
    .stApp {
        background-color: #101820;
        color: #F1F5F9;
    }

    [data-testid="stSidebar"] {
        background-color: #17232F;
    }

    [data-testid="stMetric"] {
        background-color: #1D2B38;
        padding: 18px;
        border-radius: 10px;
        border: 1px solid #344454;
    }

    [data-testid="stMetricValue"] {
        color: #38BDF8;
    }

    h1, h2, h3 {
        color: #E2E8F0;
    }

    .stDataFrame {
        border: 1px solid #344454;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# Sidebar navigation
st.sidebar.title("≡ƒÅ¡ INDUSTRIAL IoT")
st.sidebar.caption("Machine Analytics System")

page = st.sidebar.radio(
    "Navigation",
    ["Machine Overview", "Machine Analytics", "AI Assistant"]
)

st.sidebar.divider()

if st.sidebar.button("≡ƒöä Refresh Dashboard", use_container_width=True):
    st.rerun()


# API functions
def get_live_data():

    response = requests.get(
        f"{API}/machines/live",
        timeout=5
    )

    response.raise_for_status()

    return response.json().get("machines", [])


def get_summary():

    response = requests.get(
        f"{API}/machines/summary",
        timeout=10
    )

    response.raise_for_status()

    return response.json()


def get_machine_history(machine_id):

    response = requests.get(
        f"{API}/machines/{machine_id}/history",
        timeout=10
    )

    response.raise_for_status()

    return response.json().get("history", [])


# Dashboard data
try:

    live_data = get_live_data()
    summary_data = get_summary()

    live_df = pd.DataFrame(live_data)
    summary_df = pd.DataFrame(summary_data)

    if not live_df.empty:

        live_df["Machine Status"] = live_df["status"].map({
            1: "Running",
            0: "Stopped"
        })

        live_df["Stop Reason"] = live_df[
            "stop_reason_code"
        ].map(
            lambda code: STOP_REASONS.get(code, "-")
        )

        live_df["Anomaly"] = live_df.get(
            "is_anomaly",
            pd.Series(False, index=live_df.index)
        ).fillna(False)

    # =====================================
    # PAGE 1: MACHINE OVERVIEW
    # =====================================

    if page == "Machine Overview":

        st.title("Machine Overview")

        st.caption(
            "Real-time Industrial Machine Monitoring Dashboard"
        )

        if not live_df.empty:

            total_machines = len(live_df)

            running = int(
                (live_df["status"] == 1).sum()
            )

            stopped = int(
                (live_df["status"] == 0).sum()
            )

            anomalies = int(
                live_df["Anomaly"].sum()
            )

        else:

            total_machines = 0
            running = 0
            stopped = 0
            anomalies = 0

        # KPI Cards
        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total Machines",
            total_machines
        )

        col2.metric(
            "Running",
            running
        )

        col3.metric(
            "Stopped",
            stopped
        )

        col4.metric(
            "Anomalies",
            anomalies
        )

        st.divider()

        # Live machine details
        st.subheader("Live Machine Status")

        if not live_df.empty:

            display_columns = [
                "machine_id",
                "machine_name",
                "temperature",
                "power",
                "current",
                "production_count",
                "Machine Status",
                "Stop Reason"
            ]

            available_columns = [
                col for col in display_columns
                if col in live_df.columns
            ]

            st.dataframe(
                live_df[available_columns],
                use_container_width=True,
                hide_index=True
            )

            # Machine charts
            st.subheader("Machine Performance")

            chart1, chart2 = st.columns(2)

            with chart1:

                st.markdown("### Temperature")

                st.bar_chart(
                    live_df.set_index("machine_id")[
                        "temperature"
                    ]
                )

            with chart2:

                st.markdown("### Production Count")

                st.bar_chart(
                    live_df.set_index("machine_id")[
                        "production_count"
                    ]
                )

            # Anomaly section
            st.subheader("Anomaly Alerts")

            anomaly_df = live_df[
                live_df["Anomaly"]
            ]

            if not anomaly_df.empty:

                st.warning(
                    f"{len(anomaly_df)} machine reading(s) "
                    "have been flagged as anomalous."
                )

                alert_columns = [
                    col for col in [
                        "machine_id",
                        "temperature",
                        "Anomaly"
                    ]
                    if col in anomaly_df.columns
                ]

                st.dataframe(
                    anomaly_df[alert_columns],
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.success("No temperature anomalies detected.")

        else:

            st.info("Waiting for live machine data.")

        # Summary section
        st.divider()

        st.subheader("Machine Summary")

        if not summary_df.empty:

            st.dataframe(
                summary_df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info("No machine summary available.")

    # =====================================
    # PAGE 2: MACHINE ANALYTICS
    # =====================================

    elif page == "Machine Analytics":

        st.title("Machine Analytics")

        st.caption(
            "Individual Machine Performance and Historical Analysis"
        )

        if not live_df.empty:

            machine_ids = live_df["machine_id"].astype(str).tolist()

        elif not summary_df.empty:

            machine_ids = summary_df["machine_id"].astype(str).tolist()

        else:

            machine_ids = []

        if machine_ids:

            selected_machine = st.selectbox(
                "Select Machine",
                machine_ids
            )

            # Selected machine live details
            selected_data = live_df[
                live_df["machine_id"].astype(str)
                == selected_machine
            ] if not live_df.empty else pd.DataFrame()

            if not selected_data.empty:

                machine = selected_data.iloc[0]

                st.subheader(
                    f"Machine: {selected_machine}"
                )

                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "Temperature",
                    f"{machine['temperature']} ┬░C"
                )

                c2.metric(
                    "Power",
                    f"{machine.get('power', 'N/A')}"
                )

                c3.metric(
                    "Current",
                    f"{machine.get('current', 'N/A')}"
                )

                status = (
                    "Running"
                    if machine["status"] == 1
                    else "Stopped"
                )

                c4.metric(
                    "Machine Status",
                    status
                )

                stop_code = machine.get("stop_reason_code")

                if pd.notna(stop_code) and stop_code:
                    st.info(
                        "Stop Reason: "
                        + STOP_REASONS.get(stop_code, "Unknown reason")
                    )

            st.divider()

            # Historical data
            st.subheader("Historical Machine Data")

            history_data = get_machine_history(
                selected_machine
            )

            if history_data:

                history_df = pd.DataFrame(history_data)

                history_df["timestamp"] = pd.to_datetime(
                    history_df["timestamp"]
                )

                history_df = history_df.sort_values(
                    "timestamp"
                )

                history_df = history_df.set_index(
                    "timestamp"
                )

                # Temperature history
                st.markdown("### Temperature Trend")

                st.line_chart(
                    history_df["temperature"]
                )

                # Production history
                st.markdown("### Production Trend")

                st.line_chart(
                    history_df["production_count"]
                )

                # Running and stopped readings
                running_count = int(
                    (history_df["status"] == 1).sum()
                )

                stopped_count = int(
                    (history_df["status"] == 0).sum()
                )

                st.subheader("Machine Operating Status")

                c1, c2 = st.columns(2)

                c1.metric(
                    "Running Readings",
                    running_count
                )

                c2.metric(
                    "Stopped Readings",
                    stopped_count
                )

                # Anomaly history
                st.subheader("Anomaly History")

                if "is_anomaly" in history_df.columns:

                    anomaly_history = history_df[
                        history_df["is_anomaly"] == True
                    ]

                    if not anomaly_history.empty:

                        st.warning(
                            f"{len(anomaly_history)} anomalous "
                            "readings found."
                        )

                        st.dataframe(
                            anomaly_history.reset_index(),
                            use_container_width=True,
                            hide_index=True
                        )

                    else:

                        st.success("No anomalies in this history.")

                # Stop reason history
                st.subheader("Stop Reason History")

                if "stop_reason_code" in history_df.columns:

                    stopped_history = history_df[
                        history_df["stop_reason_code"].notna()
                        & (history_df["stop_reason_code"] != "")
                    ].copy()

                    if not stopped_history.empty:

                        stopped_history["Stop Reason"] = (
                            stopped_history["stop_reason_code"].map(
                                lambda code: STOP_REASONS.get(
                                    code,
                                    "Unknown reason"
                                )
                            )
                        )

                        st.dataframe(
                            stopped_history[
                                ["stop_reason_code", "Stop Reason"]
                            ].reset_index(),
                            use_container_width=True,
                            hide_index=True
                        )

                    else:

                        st.info("No stop reason records available.")

                # Complete history table
                st.subheader("Recent Machine Readings")

                st.dataframe(
                    history_df.reset_index(),
                    use_container_width=True,
                    hide_index=True
                )

            else:

                st.info(
                    "No historical data available for this machine."
                )

        else:

            st.warning("No machine data available.")
    elif page == "AI Assistant":

        render_rag_assistant(API)

except requests.RequestException as error:

    st.error(
        f"Backend connection error: {error}"
    )

except Exception as error:

    st.error(
        f"Dashboard error: {error}"
    )
