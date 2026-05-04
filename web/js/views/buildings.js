/**
 * Buildings view — thin wrapper around the shared queue view factory.
 */

import { calcBuildSpeed } from '../lib/speed.js';
import { createQueueView } from '../lib/queue_view.js';
import { rest } from '../rest.js';

export default createQueueView({
  id: 'buildings',
  title: 'Buildings',
  heading: '🏗 Buildings',
  contentId: 'buildings-content',
  loadingIcon: '▦',
  loadingText: 'Loading buildings…',
  emptyText: 'No buildings found',
  toggleId: 'hide-completed-buildings',
  queueKey: 'build_queue',
  categoryKey: 'buildings',
  storedKey: 'buildings',
  completedKeys: ['completed_buildings', 'completed_research'],
  defaultCategory: 'building',
  speedFn: calcBuildSpeed,
  progressColor: '#4fc3f7',
  actionIcon: '🔨 ',
  actionLabel: 'Build',
  actionVerb: 'building',
  msgClass: 'build-msg',
  btnClass: 'build-btn',
  successMsg: '✓ Building started!',
  apiAction: (iid) => rest.buildItem(iid),
});
