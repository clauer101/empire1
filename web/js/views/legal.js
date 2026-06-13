/**
 * Legal view — Impressum (§ 5 DDG) + Privacy Notice (GDPR/DSGVO).
 */

import { pageTitle } from '../lib/page_title.js';

let container;

function init(el) {
  container = el;
}

function enter() {
  pageTitle.set('Legal');
  container.innerHTML = `
    <div style="max-width:620px;margin:32px auto;padding:0 16px 48px;">

      <h2 style="margin-bottom:24px;">Legal</h2>

      <!-- ── Impressum ── -->
      <h3 style="font-size:1rem;margin-bottom:12px;color:var(--text-dim);text-transform:uppercase;letter-spacing:.05em;font-size:11px;">Impressum (§ 5 DDG)</h3>
      <p style="margin:0 0 6px;">Christoph Lauer</p>
      <p style="margin:0 0 6px;">Oberringstraße 27a<br>85051 Ingolstadt<br>Deutschland</p>
      <p style="margin:0 0 6px;">E-Mail: <a href="mailto:lauer.christoph@gmail.com" style="color:var(--accent);">lauer.christoph@gmail.com</a></p>
      <p style="margin:0 0 24px;font-size:0.88em;color:var(--text-dim);">Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV: Christoph Lauer, Anschrift wie oben.</p>

      <hr style="border:none;border-top:1px solid rgba(255,255,255,0.08);margin:24px 0;">

      <!-- ── Privacy / DSGVO ── -->
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
        <h3 style="margin:0;font-size:11px;color:var(--text-dim);text-transform:uppercase;letter-spacing:.05em;">Privacy Notice (GDPR / DSGVO)</h3>
        <div style="display:flex;gap:6px;">
          <button id="legal-lang-en" style="padding:2px 10px;font-size:12px;cursor:pointer;border:1px solid var(--accent,#4fc3f7);background:var(--accent,#4fc3f7);color:#000;border-radius:4px;">EN</button>
          <button id="legal-lang-de" style="padding:2px 10px;font-size:12px;cursor:pointer;border:1px solid var(--accent,#4fc3f7);background:transparent;color:var(--accent,#4fc3f7);border-radius:4px;">DE</button>
        </div>
      </div>

      <div id="legal-en">
        <p>When you register, we collect your <strong>username</strong>, your <strong>e-mail address</strong> (optional), and an encrypted password.</p>

        <h4 style="margin:18px 0 6px;">Legal basis</h4>
        <p>Your data is processed on the basis of <strong>Art. 6(1)(b) GDPR</strong> (performance of a contract). Without a username the game account cannot be created or managed. No separate consent is required under this legal basis.</p>

        <h4 style="margin:18px 0 6px;">Purpose of processing</h4>
        <ul style="padding-left:20px;line-height:1.8;">
          <li>Creating and managing your user account</li>
          <li>Authentication at login</li>
          <li>Account recovery (e-mail, if provided)</li>
          <li>Delivery of web push notifications (if subscribed)</li>
        </ul>

        <h4 style="margin:18px 0 6px;">Retention</h4>
        <p>Your data is stored for as long as your account is active. After deletion it is removed without undue delay.</p>

        <h4 style="margin:18px 0 6px;">Your rights</h4>
        <p>Under the GDPR you have the right of <strong>access</strong>, <strong>rectification</strong>, <strong>erasure</strong>, <strong>restriction of processing</strong>, and <strong>data portability</strong>. Contact: <a href="mailto:lauer.christoph@gmail.com" style="color:var(--accent);">lauer.christoph@gmail.com</a></p>
      </div>

      <div id="legal-de" style="display:none;">
        <p>Bei der Registrierung erheben wir deinen <strong>Benutzernamen</strong>, deine <strong>E-Mail-Adresse</strong> (optional) sowie ein verschlüsseltes Passwort.</p>

        <h4 style="margin:18px 0 6px;">Rechtsgrundlage</h4>
        <p>Die Verarbeitung erfolgt auf Grundlage von <strong>Art. 6 Abs. 1 lit. b DSGVO</strong> (Vertragserfüllung). Ohne Benutzernamen kann das Spielkonto nicht angelegt oder verwaltet werden. Eine gesonderte Einwilligung ist nach dieser Rechtsgrundlage nicht erforderlich.</p>

        <h4 style="margin:18px 0 6px;">Zweck der Verarbeitung</h4>
        <ul style="padding-left:20px;line-height:1.8;">
          <li>Anlage und Verwaltung deines Benutzerkontos</li>
          <li>Authentifizierung beim Login</li>
          <li>Kontowiederherstellung (E-Mail, sofern angegeben)</li>
          <li>Zustellung von Web-Push-Benachrichtigungen (bei Anmeldung)</li>
        </ul>

        <h4 style="margin:18px 0 6px;">Speicherdauer</h4>
        <p>Deine Daten werden gespeichert, solange dein Konto aktiv ist. Nach Löschung werden sie ohne unangemessene Verzögerung entfernt.</p>

        <h4 style="margin:18px 0 6px;">Deine Rechte</h4>
        <p>Du hast nach der DSGVO das Recht auf <strong>Auskunft</strong>, <strong>Berichtigung</strong>, <strong>Löschung</strong>, <strong>Einschränkung der Verarbeitung</strong> sowie <strong>Datenübertragbarkeit</strong>. Kontakt: <a href="mailto:lauer.christoph@gmail.com" style="color:var(--accent);">lauer.christoph@gmail.com</a></p>
      </div>

    </div>
  `;

  container.querySelector('#legal-lang-en').addEventListener('click', () => _setLang('en'));
  container.querySelector('#legal-lang-de').addEventListener('click', () => _setLang('de'));
}

function _setLang(lang) {
  container.querySelector('#legal-en').style.display = lang === 'en' ? '' : 'none';
  container.querySelector('#legal-de').style.display = lang === 'de' ? '' : 'none';
  container.querySelector('#legal-lang-en').style.background = lang === 'en' ? 'var(--accent,#4fc3f7)' : 'transparent';
  container.querySelector('#legal-lang-en').style.color = lang === 'en' ? '#000' : 'var(--accent,#4fc3f7)';
  container.querySelector('#legal-lang-de').style.background = lang === 'de' ? 'var(--accent,#4fc3f7)' : 'transparent';
  container.querySelector('#legal-lang-de').style.color = lang === 'de' ? '#000' : 'var(--accent,#4fc3f7)';
}

function leave() {}

export default { id: 'legal', title: 'Legal', init, enter, leave };
