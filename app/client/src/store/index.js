import Vue from 'vue';
import Vuex from 'vuex';

import correspondents from './modules/correspondents';
import document from './modules/document';
import institutions from './modules/institutions';
import languages from './modules/languages';
import user from './modules/user';
import changelog from './modules/changelog';
import locks from './modules/locks';
import witnesses from './modules/witnesses';
import bookmarks from './modules/bookmarks';

Vue.use(Vuex);

export default new Vuex.Store({
    modules: {
      correspondents,
      document,
      institutions,
      languages,
      user,
      changelog,
      locks,
      witnesses,
      bookmarks
    }
});
