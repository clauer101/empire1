/**
 * Research view — thin wrapper around the shared queue view factory.
 */

import { calcResearchSpeed } from '../lib/speed.js';
import { createQueueView } from '../lib/queue_view.js';
import { rest } from '../rest.js';

export default createQueueView({
  id:             'research',
  title:          'Research',
  heading:        '🔬 Research',
  contentId:      'research-content',
  loadingIcon:    '◉',
  loadingText:    'Loading research…',
  emptyText:      'No research found',
  toggleId:       'hide-completed-research',
  queueKey:       'research_queue',
  categoryKey:    'knowledge',
  storedKey:      'knowledge',
  completedKeys:  ['completed_research', 'completed_buildings'],
  defaultCategory:'knowledge',
  speedFn:        calcResearchSpeed,
  progressColor:  '#ffa726',
  actionIcon:     '🔬 ',
  actionLabel:    'Research',
  actionVerb:     'researching',
  msgClass:       'research-msg',
  btnClass:       'research-btn',
  successMsg:     '✓ Research started!',
  apiAction:      (iid) => rest.buildItem(iid),
});
