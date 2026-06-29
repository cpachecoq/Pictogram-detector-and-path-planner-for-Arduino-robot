COMMAND_STABLE_FRAMES = 3
MAX_MISSING_FRAMES = 5


class MovementController:
    def __init__(self):
        self.stable_command = "STOP"
        self.candidate_command = None
        self.candidate_count = 0
        self.missing_frames = 0
        self.state = "WAITING"

    def update(self, raw_command, has_valid_detection=True, robot_safe=True):
        if not robot_safe:
            self.state = "UNSAFE"
            return "STOP", "STOP", self.state

        if not has_valid_detection or raw_command is None:
            self.missing_frames += 1

            if self.missing_frames >= MAX_MISSING_FRAMES:
                self.stable_command = "STOP"
                self.state = "LOST"

            return raw_command, self.stable_command, self.state

        self.missing_frames = 0

        stable_command = self.filter_command(raw_command)
        self.state = self.get_state(stable_command)

        return raw_command, stable_command, self.state

    def filter_command(self, raw_command):
        if raw_command == self.stable_command:
            self.candidate_command = None
            self.candidate_count = 0
            return self.stable_command

        if raw_command == self.candidate_command:
            self.candidate_count += 1
        else:
            self.candidate_command = raw_command
            self.candidate_count = 1

        if self.candidate_count >= COMMAND_STABLE_FRAMES:
            self.stable_command = raw_command
            self.candidate_command = None
            self.candidate_count = 0

        return self.stable_command

    def get_state(self, command):
        if command == "STOP":
            return "STOPPED"
        if command in ["LEFT", "RIGHT"]:
            return "ALIGNING"
        if command == "FORWARD":
            return "MOVING"
        return "WAITING"