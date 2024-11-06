**Summary Query: Probabilistic Roadmaps and RRT Algorithms in Robotics Manipulation**Probabilistic Roadmaps (PRM) and Rapidly-exploring Random Trees (RRT) are two influential algorithms in the field of robot motion planning. They are particularly effective in high-dimensional spaces, making them valuable for robotic manipulation tasks.

### Probabilistic Roadmaps (PRM)

**Overview:**
- PRM is a planning algorithm that constructs a roadmap of the free space by sampling random configurations and connecting them with simple paths.
- It's particularly useful for multi-query problems, where the same environment is queried multiple times for different start and end configurations.

**Steps:**
1. **Sampling:** Randomly sample a set of configurations from the free space.
2. **Node Addition:** Add these configurations as nodes to the roadmap if they are valid (i.e., not in collision with obstacles).
3. **Connection:** Attempt to connect each node to its nearest neighbors using a simple path planner (e.g., straight-line motion). Only valid connections (those not in collision) are added as edges.
4. **Query:** Once the roadmap is constructed, path planning between two configurations involves adding them to the roadmap and finding a path through graph search algorithms like A* or Dijkstra.

**Advantages:**
- Suitable for high-dimensional configuration spaces.
- Allows for reuse of the roadmap for multiple queries, making it efficient for problems where the environment does not change.

**Disadvantages:**
- The quality of the roadmap heavily depends on the sampling and connection strategies.
- Not suited for environments that change frequently or require fast online adaption.

### Rapidly-exploring Random Trees (RRT)

**Overview:**
- RRT is a single-query, incremental path planning algorithm designed to efficiently search nonconvex, high-dimensional spaces by randomly sampling the space and building a tree that explores it.
- It's particularly effective for planning in complex and dynamic environments, such as those encountered in robotic manipulation.

**Steps:**
1. **Initialize:** Start with an initial configuration as the root of the tree.
2. **Random Sampling:** Randomly sample a point in the configuration space.
3. **Nearest Node:** Find the node in the tree that is closest to the sampled point.
4. **Extend:** Extend the tree towards the sampled point. This is usually done by moving a small step from the nearest node towards the sample.
5. **Collision Check:** If this new node is in the free space and not in collision, add it to the tree.
6. **Repeat:** Continue the process until you reach the goal configuration or a predefined number of iterations.

**Advantages:**
- Highly efficient for finding feasible paths in spaces with obstacles.
- Naturally handles high-dimensional spaces due to its tree-growing strategy.

**Disadvantages:**
- Results in paths that can be suboptimal. Post-processing might be necessary for path smoothing.
- The exploration is more biased towards regions far from the tree, which can sometimes lead to less thorough exploration of nearby space.

### Application in Robotic Manipulation

Both PRM and RRT are powerful tools for robotic manipulation tasks, which often require navigating complex environments with many degrees of freedom. Here's how they are useful:

- **High Dimensionality:** Robotic manipulators have multiple joints and constraints, leading to high-dimensional configuration spaces. Both PRM and RRT are well-suited to handle these complexities.
  
- **Collision Avoidance:** By sampling and extending through free space, these algorithms naturally incorporate collision checking, ensuring that manipulation paths do not intersect with obstacles.

- **Adaptability:** In changing environments, RRT can be adapted to find new paths quickly, while PRM can be rebuilt or updated as necessary.

- **Multi-query Situations:** In assembly lines or tasks where the robot frequently needs to move between fixed points, PRM's roadmap approach provides significant efficiencies by allowing reuse of the pathways.

- **Dynamic and Unstructured Environments:** RRT's incremental nature makes it a good candidate for dynamic environments where obstacles and goals might change or move.

Overall, PRM and RRT provide foundational frameworks in robotic motion planning, allowing robots to perform sophisticated manipulation tasks that require navigating complex environments while ensuring safety and efficiency.