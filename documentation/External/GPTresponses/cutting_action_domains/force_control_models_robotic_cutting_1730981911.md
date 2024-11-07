**Query Summary:** Discuss the importance of force-control models in robotics, specifically for cutting actions, and explain how impedance and admittance control are used to regulate cutting force in response to material resistance.Force-control models are essential in robotic actions like cutting because they ensure that the robot applies the appropriate amount of force to achieve the desired outcome. These models are used to dynamically adjust the robot's actions in response to changes in the environment, such as varying material resistance during a cutting task. In robotic cutting, maintaining an appropriate cutting force is crucial to ensure precision, prevent damage to the tool or material, and achieve high-quality results.

### Impedance and Admittance Control

Robotics often utilizes impedance and admittance control strategies to adjust the cutting force in real time. Both methods deal with how a robot responds to force and position changes but differ in their approach and application within a robotic control system.

#### Impedance Control

- **Concept**: Impedance control is primarily concerned with defining a desired dynamic relationship between force and motion. It controls the mechanical impedance of the robot—its apparent stiffness, damping, and inertia—leading to a specific response when interacting with the environment.
  
- **Application**: In the context of robotic cutting, impedance control allows the robot to adjust its movement in response to force feedback. If the material resistance increases (e.g., hitting a denser area), the impedance controller would adjust the robot's trajectory and velocity to maintain the desired force, thereby enabling smooth and consistent cutting.

- **Advantages**: This control strategy is well-suited for tasks where maintaining precise force levels is crucial, and it can tolerate variations in environmental properties, such as changes in material density during the cutting process.

#### Admittance Control

- **Concept**: Admittance control is essentially the inverse of impedance control. Instead of directly controlling the robot's dynamics, it regulates how force applied to the robot results in motion. It translates force feedback into motion commands.

- **Application**: During cutting, if the robot encounters a change in material resistance, an admittance controller takes the external force and translates it into a position or velocity change that adjusts cutting action to maintain the desired force level.

- **Advantages**: Admittance control is particularly useful for robots with high structure stiffness or when a more pronounced reaction to sensed forces is needed. It allows for more adaptable interactions in environments with varying forces.

### Real-time Adjustment

Implementing either strategy involves sensors (such as force/torque sensors) that supply real-time feedback about the force exerted on the material. The control system processes this information and dynamically adjusts the robot's movements or exerted forces accordingly. By doing so, these force-control models help maintain tool stability, optimize cutting efficiency, ensure safety, and improve the overall quality of the cut even in the face of variations in material properties.

In summary, force-control models, using impedance and admittance control strategies, enable robots to perform complex tasks like cutting with precision by allowing them to adapt in real time to changes in material resistance, ultimately leading to better performance and results in automated cutting applications.