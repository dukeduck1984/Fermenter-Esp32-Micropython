class FermenterPID:
    def __init__(self, kp=2, ki=0.0001, kd=2):
        self.k_p = float(kp)
        self.k_i = float(ki)
        self.k_d = float(kd)
        self.last_error = 0
        self.integration = 0
        self.last_output = 0

    def update(self, temp, setpoint):
        """
        temp: float; real-time temperature measured by ds18 sensor
        setpoint: float; target temperature to achieve
        return: float; temperature correction
        """
        error = setpoint - temp
        if self.last_error == 0:
            self.last_error = error #catch first run error

        P_value = self.k_p * error
        D_value = -(self.k_d * (error - self.last_error))
        self.last_error = error
        if -15 < self.last_output < 15:
            self.integration = self.integration + error

        I_value = self.integration * self.k_i

        self.last_output = max(min(P_value + I_value + D_value, 15), -15)
        return self.last_output

