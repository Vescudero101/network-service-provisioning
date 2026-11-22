## L2 VLAN

Choose **Deploy** or **Cease**: each one has its own form.

**Deploy** creates a VLAN on every switch of its path.
You need a service reference (for example `CUST1-V200`), the VLAN ID and the VLAN name.
The path (which switches and ports) comes from the path script.

**Cease** removes a VLAN. You need the service reference and the VLAN ID only:
the path script finds where the VLAN is today.

*The path scripts are placeholders for now: they return dummy data (SW1 and SW2, trunk Gi1/1).*

**Start** is a real run (it asks you to confirm before pushing). **Dry run** stops after the plan and pushes nothing.
