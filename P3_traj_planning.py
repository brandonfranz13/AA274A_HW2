import numpy as np
from P1_astar import DetOccupancyGrid2D, AStar
from P2_rrt import *
import scipy.interpolate
import matplotlib.pyplot as plt
from HW1.P1_differential_flatness import *
from HW1.P2_pose_stabilization import *
from HW1.P3_trajectory_tracking import *

class SwitchingController(object):
    """
    Uses one controller to initially track a trajectory, then switches to a 
    second controller to regulate to the final goal.
    """
    def __init__(self, traj_controller, pose_controller, t_before_switch):
        self.traj_controller = traj_controller
        self.pose_controller = pose_controller
        self.t_before_switch = t_before_switch

    def compute_control(self, x, y, th, t):
        """
        Inputs:
            (x,y,th): Current state 
            t: Current time

        Outputs:
            V, om: Control actions
        """
        ########## Code starts here ##########
        if t < (self.traj_times[-1] - self.t_before_switch):
            [V,om] = self.traj_controller.compute_control(x, y, th, t)
        else:
            [V,om] = self.pose_controller.compute_control(x, y, th, t)

        ########## Code ends here ##########

def compute_smoothed_traj(path, V_des, alpha, dt):
    """
    Fit cubic spline to a path and generate a resulting trajectory for our
    wheeled robot.

    Inputs:
        path (np.array [N,2]): Initial path
        V_des (float): Desired nominal velocity, used as a heuristic to assign nominal
            times to points in the initial path
        alpha (float): Smoothing parameter (see documentation for
            scipy.interpolate.splrep)
        dt (float): Timestep used in final smooth trajectory
    Outputs:
        traj_smoothed (np.array [N,7]): Smoothed trajectory
        t_smoothed (np.array [N]): Associated trajectory times
    Hint: Use splrep and splev from scipy.interpolate
    """
    ########## Code starts here ##########
    # import pdb; pdb.set_trace()
    path = np.array(path)
    t = np.zeros(len(path))
    for i in range(len(path)-1):
        t[i+1] = t[i] + np.linalg.norm(path[i+1,:] - path[i,:]) / V_des
    t_max = t[-1]
    t_smoothed = np.arange(0.0, t_max, dt)
    traj_smoothed = np.zeros((len(t_smoothed), 7))
    sply = scipy.interpolate.splrep(x=t, y=path[:,1], s=alpha)
    splx = scipy.interpolate.splrep(x=t, y=path[:,0], s=alpha)
    
    traj_smoothed[:, 0] = scipy.interpolate.splev(t_smoothed, splx, der=0)
    traj_smoothed[:, 1] = scipy.interpolate.splev(t_smoothed, sply, der=0)
    traj_smoothed[:, 2] = np.arctan2(traj_smoothed[:,1], traj_smoothed[:,0])
    traj_smoothed[:, 3] = scipy.interpolate.splev(t_smoothed, splx, der=1)
    traj_smoothed[:, 4] = scipy.interpolate.splev(t_smoothed, sply, der=1)
    traj_smoothed[:, 5] = scipy.interpolate.splev(t_smoothed, splx, der=2)
    traj_smoothed[:, 6] = scipy.interpolate.splev(t_smoothed, sply, der=2)
    
    ########## Code ends here ##########

    return traj_smoothed, t_smoothed

def modify_traj_with_limits(traj, t, V_max, om_max, dt):
    """
    Modifies an existing trajectory to satisfy control limits and
    interpolates for desired timestep.

    Inputs:
        traj (np.array [N,7]): original trajecotry
        t (np.array [N]): original trajectory times
        V_max, om_max (float): control limits
        dt (float): desired timestep
    Outputs:
        t_new (np.array [N_new]) new timepoints spaced dt apart
        V_scaled (np.array [N_new])
        om_scaled (np.array [N_new])
        traj_scaled (np.array [N_new, 7]) new rescaled traj at these timepoints
    Hint: This should almost entirely consist of calling functions from Problem Set 1
    """
    ########## Code starts here ##########
    s_f = State(x = traj[-1, 0], y = traj[-1, 0], V = V_max, th=-np.pi/2)
    
    V,om = compute_controls(traj=traj)
    s = compute_arc_length(V, t)
    V_tilde = rescale_V(V, om, V_max, om_max)
    tau = compute_tau(V_tilde, s)
    om_tilde = rescale_om(V, om, V_scaled)
    
    t_new, V_scaled, om_scaled, traj_scaled = interpolate_traj(traj, tau, V_tilde, om_tilde, dt, s_f)
    
    ########## Code ends here ##########

    return t_new, V_scaled, om_scaled, traj_scaled
