# Copyright 2020 The tfaip authors. All Rights Reserved.
#
# This file is part of tfaip.
#
# tfaip is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# tfaip is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# tfaip. If not, see http://www.gnu.org/licenses/.
# ==============================================================================
from drone.generate import all_tests, generate_drone_cfg, drone_cfg_file_path
import difflib


if __name__ == '__main__':
    # Validate the drone file
    # 1. Check if all tests are listed (this is a typical error)
    # 2. Check afterwards if the file content is identical (this happens if generate.py changed)
    import yaml
    with open(drone_cfg_file_path, 'r') as f:
        remote_drone_cfg = list(yaml.safe_load_all(f))

    # test first pipeline
    def test_pipeline_for_all_tests(idx):
        test_cmd_prefix = 'python -m unittest test'
        test_steps = [step for step in remote_drone_cfg[idx]['steps'] if any(test_cmd_prefix in cmd for cmd in step['commands'])]
        test_steps_names = [[cmd for cmd in step['commands'] if test_cmd_prefix in cmd][0].split()[-1] for step in test_steps]

        # first check if tests are all listed, this are expected errors if new tests were added
        target_tests = set(t.id() for t in all_tests)
        set_tests = set(test_steps_names)

        not_listed = target_tests.symmetric_difference(set_tests)
        if not_listed:
            raise Exception(f"Some tests are not included in drone {not_listed}. "
                            f"Please rerun `drone/generate.py` to update the .drone.yml automatically!")

    [test_pipeline_for_all_tests(i) for i in [0, 1]]

    # now test if the yml dicts are identical
    # this can happen if anything else changed in the file
    local_drone_cfg = generate_drone_cfg()

    if local_drone_cfg != remote_drone_cfg:
        yaml.dump(local_drone_cfg)
        diff = "\n".join([str(diff) for diff in difflib.unified_diff(
            yaml.dump(local_drone_cfg, default_flow_style=False, sort_keys=False).split('\n'),
            yaml.dump(remote_drone_cfg, default_flow_style=False, sort_keys=False).split('\n'))])
        raise Exception(f"The drone config changed. Possible drone/generate.py was updated but not called."
                        f"Please rerun `drone/generate.py` to update the .drone.yml automatically\n\n"
                        f"{diff}")
