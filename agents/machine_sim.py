import random

class MachineSimulator:
    def simulate_status(self, machines):
        """
        Randomly return 'OK' or 'FAIL' for each machine
        """
        status = {}
        for m in machines:
            status[m] = random.choice(["OK", "OK", "OK", "FAIL"])  # 25% failure
        return status

    def fail_machine(self, machines_dict, machine_id):
        """
        Deterministically set a specific machine to FAIL status.

        Args:
            machines_dict: dict of machine configs from factory state
            machine_id: the machine to fail

        Returns:
            dict of machine statuses after the failure
        """
        status = {}
        for m_id in machines_dict:
            if m_id == machine_id:
                status[m_id] = "FAIL"
            else:
                status[m_id] = machines_dict[m_id].get("status", "OK")
                if status[m_id] == "available":
                    status[m_id] = "OK"
                elif status[m_id] == "failed":
                    status[m_id] = "FAIL"
        return status

    def recover_machine(self, machines_dict, machine_id):
        """
        Deterministically set a specific machine back to OK status.

        Args:
            machines_dict: dict of machine configs from factory state
            machine_id: the machine to recover

        Returns:
            dict of machine statuses after the recovery
        """
        status = {}
        for m_id in machines_dict:
            if m_id == machine_id:
                status[m_id] = "OK"
            else:
                status[m_id] = machines_dict[m_id].get("status", "OK")
                if status[m_id] == "available":
                    status[m_id] = "OK"
                elif status[m_id] == "failed":
                    status[m_id] = "FAIL"
        return status
