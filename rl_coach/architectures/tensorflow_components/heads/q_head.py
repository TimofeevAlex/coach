#
# Copyright (c) 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import tensorflow as tf

from rl_coach.architectures.tensorflow_components.layers import Dense
from rl_coach.architectures.tensorflow_components.heads.head import Head
from rl_coach.base_parameters import AgentParameters
from rl_coach.core_types import QActionStateValue
from rl_coach.spaces import SpacesDefinition, BoxActionSpace, DiscreteActionSpace


class QHead(Head):
    def __init__(self, agent_parameters: AgentParameters, spaces: SpacesDefinition, network_name: str,
                 head_idx: int = 0, loss_weight: float = 1., is_local: bool = True, activation_function: str='relu',
                 dense_layer=Dense):
        super().__init__(agent_parameters, spaces, network_name, head_idx, loss_weight, is_local, activation_function,
                         dense_layer=dense_layer)
        self.name = 'q_values_head'
        if isinstance(self.spaces.action, BoxActionSpace):
            self.num_actions = 1
        elif isinstance(self.spaces.action, DiscreteActionSpace):
            self.num_actions = len(self.spaces.action.actions)
        else:
            raise ValueError(
                'QHead does not support action spaces of type: {class_name}'.format(
                    class_name=self.spaces.action.__class__.__name__,
                )
            )
        self.return_type = QActionStateValue
        if agent_parameters.network_wrappers[self.network_name].replace_mse_with_huber_loss:
            self.loss_type = tf.losses.huber_loss
        else:
            self.loss_type = tf.losses.mean_squared_error

    def _build_module(self, input_layer):
        # Standard Q Network
        self.q_values = self.output = tf.layers.dense(input_layer, name='output', units=18)#self.dense_layer(self.num_actions)(input_layer, name='output'))#
        # used in batch-rl to estimate a probablity distribution over actions
        self.softmax = self.add_softmax_with_temperature()

    def __str__(self):
        result = [
            "Dense (num outputs = {})".format(self.num_actions)
        ]
        return '\n'.join(result)

    def add_softmax_with_temperature(self):
        temperature = self.ap.network_wrappers[self.network_name].softmax_temperature
        temperature_scaled_outputs = self.q_values / temperature
        return tf.nn.softmax(temperature_scaled_outputs, name="softmax")

