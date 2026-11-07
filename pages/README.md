# pages/

One Streamlit page per question. File name sets the sidebar order: `1_machines.py`, `2_demand.py`,
`3_downtime.py`, `4_players.py`, `5_comps.py`, `6_actions.py`, `7_model.py`.

Pattern:
```python
import streamlit as st
from royale import io, money          # pages read marts only, never DATA_DIR
df = io.mart("q2_demand")             # built by royale/marts/q2_demand.py
```
Every page needs: a period filter, one drill (bank, zone, guest group), and a "Source" expander that
names the mart and the query behind each number so a judge can trace it.
