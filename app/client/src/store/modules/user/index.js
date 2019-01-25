import {http, baseApiURL} from '../../../modules/http-common';
import {getRoles} from '../../../modules/document-helpers';

const state = {
  current_user: null
};

const mutations = {
  UPDATE_USER (state, {data, included}) {
    console.log('UPDATE_USER', data);
    if (!data) {
      state.current_user = null;
    } else {
      state.current_user = {
        ...data.attributes,
        roles: getRoles(included)
      };
    }
  }
};

const actions = {

  fetchCurrent ({ commit }) {
    return http.get("token/refresh")
      .then(response => {
        if (response.data && response.data.user) {
          const user_api_url = response.data.user.replace(baseApiURL, '');
          http.get(`${user_api_url}?include=roles&without-relationships`).then( response => {
            commit('UPDATE_USER', response.data);
          })
        } else {
          commit('UPDATE_USER', {data: null});
        }
      }).catch(error => {
        commit('UPDATE_USER', {data: null});
        reject(error)
      });
  },
  /*
  save ({ commit, rootGetters }, data) {
    return http.put(`/documents`, { data: data })
      .then(response => {
        commit('UPDATE_DOCUMENT', response.data.data);
        resolve(response.data)
      })
      .catch(error => {
        console.error("error", error);
        reject(error)
      })
  },
  */
};

const getters = {


};

const userModule = {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
};

export default userModule;
