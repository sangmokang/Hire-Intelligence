import { authHandlers } from './auth';
import { dashboardHandlers } from './dashboard';
import { userHandlers } from './user';

export const handlers = [...authHandlers, ...dashboardHandlers, ...userHandlers];
