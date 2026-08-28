import { ApiClient } from "./api.js";

export class AuthManager {
  constructor(onAuthChange) {
    this.currentUser = null;
    this.onAuthChange = onAuthChange;
    this.init();
  }

  async init() {
    this.currentUser = await ApiClient.getMe();
    this.notify();
  }

  notify() {
    if (this.onAuthChange) {
      this.onAuthChange(this.currentUser);
    }
  }

  async login(email, password) {
    const res = await ApiClient.login(email, password);
    this.currentUser = res.user;
    this.notify();
    return res;
  }

  async register(email, password, fullName) {
    const res = await ApiClient.register(email, password, fullName);
    this.currentUser = res.user;
    this.notify();
    return res;
  }

  async logout() {
    await ApiClient.logout();
    this.currentUser = null;
    this.notify();
  }

  async forgotPassword(email) {
    return await ApiClient.forgotPassword(email);
  }

  async resetPassword(token, newPassword) {
    return await ApiClient.resetPassword(token, newPassword);
  }
}
