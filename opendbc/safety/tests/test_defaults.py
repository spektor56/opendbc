#!/usr/bin/env python3
import unittest

import opendbc.safety.tests.common as common
from opendbc.car.structs import CarParams
from opendbc.safety import ALTERNATIVE_EXPERIENCE
from opendbc.safety.tests.libsafety import libsafety_py


class TestDefaultRxHookBase(common.PandaSafetyTest):
  FWD_BUS_LOOKUP = {}

  def test_rx_hook(self):
    # default rx hook allows all msgs
    for bus in range(4):
      for addr in self.SCANNED_ADDRS:
        self.assertTrue(self._rx(common.make_msg(bus, addr, 8)), f"failed RX {addr=}")


class TestNoOutput(TestDefaultRxHookBase):
  TX_MSGS = []

  def setUp(self):
    self.safety = libsafety_py.libsafety
    self.safety.set_safety_hooks(CarParams.SafetyModel.noOutput, 0)
    self.safety.init_tests()


class TestSilent(TestNoOutput):
  """SILENT uses same hooks as NOOUTPUT"""

  def setUp(self):
    self.safety = libsafety_py.libsafety
    self.safety.set_safety_hooks(CarParams.SafetyModel.silent, 0)
    self.safety.init_tests()


class TestAllOutput(TestDefaultRxHookBase):
  # Allow all messages
  TX_MSGS = [[addr, bus] for addr in common.PandaSafetyTest.SCANNED_ADDRS
             for bus in range(4)]

  def setUp(self):
    self.safety = libsafety_py.libsafety
    self.safety.set_safety_hooks(CarParams.SafetyModel.allOutput, 0)
    self.safety.init_tests()

  def test_spam_can_buses(self):
    # asserts tx allowed for all scanned addrs
    for bus in range(4):
      for addr in self.SCANNED_ADDRS:
        should_tx = [addr, bus] in self.TX_MSGS
        self.assertEqual(should_tx, self._tx(common.make_msg(bus, addr, 8)), f"allowed TX {addr=} {bus=}")

  def test_default_controls_not_allowed(self):
    # controls always allowed
    self.assertTrue(self.safety.get_controls_allowed())

  def test_tx_hook_on_wrong_safety_mode(self):
    # No point, since we allow all messages
    pass

  #test base implementation of rx_hook
  def test_resume_lkas_after_brake(self):
    # Test the alternative_experience flag ALT_EXP_RESUME_LKAS_AFTER_BRAKE

    # Scenario 1: LKAS resume OFF
    self.safety.set_alternative_experience(0)
    self.safety.set_controls_allowed(True)
    self.safety.set_brake_pressed_prev(False)
    self.safety.set_brake_pressed(True)

    self._rx(common.make_msg(0, 0, 8))
    self.assertFalse(self.safety.get_controls_allowed(), "Controls should be disallowed after brake press")

    self.safety.set_brake_pressed(False)

    self._rx(common.make_msg(0, 0, 8))
    self.assertFalse(self.safety.get_controls_allowed(), "Controls should remain disallowed (LKAS resume OFF)")

    # Scenario 2: LKAS resume ON
    self.safety.set_alternative_experience(ALTERNATIVE_EXPERIENCE.RESUME_LKAS_AFTER_BRAKE)
    self.safety.set_controls_allowed(True)
    self.safety.set_vehicle_moving(False)
    self.safety.set_brake_pressed(True)

    self._rx(common.make_msg(0, 0, 8))
    self.assertFalse(self.safety.get_controls_allowed(), "Controls should be disallowed after brake press")

    self.safety.set_brake_pressed(False)

    self._rx(common.make_msg(0, 0, 8))
    self.assertTrue(self.safety.get_controls_allowed(), "Controls should be allowed (LKAS resume ON)")

class TestAllOutputPassthrough(TestAllOutput):
  FWD_BLACKLISTED_ADDRS = {}
  FWD_BUS_LOOKUP = {0: 2, 2: 0}

  def setUp(self):
    self.safety = libsafety_py.libsafety
    self.safety.set_safety_hooks(CarParams.SafetyModel.allOutput, 1)
    self.safety.init_tests()


if __name__ == "__main__":
  unittest.main()
