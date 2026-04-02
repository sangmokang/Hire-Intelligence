import { authHandlers } from './auth';
import { dashboardHandlers } from './dashboard';
import { userHandlers } from './user';
import { paymentHandlers } from './payment';

export const handlers = [...authHandlers, ...dashboardHandlers, ...userHandlers, ...paymentHandlers];
