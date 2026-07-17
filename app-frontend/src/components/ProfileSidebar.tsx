import type { UserProfile } from "../types/auth";
import type {
  TrustedContactResponse,
  ProviderResponse,
} from "../types/features";
import "./MedicalHistoryModals/Modal.css";
import "../main.css";

export interface UserSettings {
  allow_trusted_contacts: boolean;
  allow_mychart_integration: boolean;
  enable_reminders: boolean;
}

interface ProfileSidebarProps {
  profile?: UserProfile;
  contacts: TrustedContactResponse[];
  providers: ProviderResponse[];
  settings?: UserSettings;

  onEditProfile: () => void;
  onEditContact: (contact: TrustedContactResponse | null) => void;
  onEditProvider: (provider: ProviderResponse | null) => void;
  onEditSettings: () => void;
}

export default function ProfileSidebar({
  profile,
  contacts,
  providers,
  settings,
  onEditProfile,
  onEditContact,
  onEditProvider,
  onEditSettings,
}: ProfileSidebarProps) {
  return (
    <aside className="sidebar">
      <h1 className="sidebar-title">Profile</h1>

      {/* USER INFO */}
      <div className="sidebar-section">
        <div className="sidebar-header">
          <h2>User Information</h2>
          <button className="edit-button" onClick={onEditProfile}>
            edit
          </button>
        </div>

        <p>
          Name: {profile?.full_name ?? "Unknown"} <br />
          Email: {profile?.email ?? "Unknown"} <br />
          Preferred Language: {profile?.preferred_language ?? "Unknown"} <br />
          Explanation Level: {profile?.explanation_level ?? "Unknown"}
        </p>
      </div>

      {/* TRUSTED CONTACTS */}
      <div className="sidebar-section">
        <div className="sidebar-header">
          <h2>Trusted Contacts</h2>
          <button className="edit-button" onClick={() => onEditContact(null)}>
            + add contact
          </button>
        </div>

        {contacts.length ? (
          contacts.map((c) => (
            <div key={c.id} className="list-row">
              <span>
                {c.contact_name} ({c.contact_email}) — {c.access_level}
              </span>
              <button className="edit-button" onClick={() => onEditContact(c)}>
                edit
              </button>
            </div>
          ))
        ) : (
          <p>No trusted contacts added yet.</p>
        )}
      </div>

      {/* PROVIDERS */}
      <div className="sidebar-section">
        <div className="sidebar-header">
          <h2>Medical Contacts</h2>
          <button className="edit-button" onClick={() => onEditProvider(null)}>
            + add provider
          </button>
        </div>

        {providers.length ? (
          providers.map((p) => (
            <div key={p.id} className="list-row">
              <span>
                {p.specialty ?? "General"}: {p.name}
              </span>
              <button className="edit-button" onClick={() => onEditProvider(p)}>
                edit
              </button>
            </div>
          ))
        ) : (
          <p>No providers on file.</p>
        )}
      </div>

      {/* SETTINGS — MATCHES BACKEND */}
      <div className="sidebar-section">
        <div className="sidebar-header">
          <h3>Account Settings</h3>
          <button className="edit-button" onClick={onEditSettings}>
            edit
          </button>
        </div>

        <p>
          Trusted Contacts:{" "}
          {settings?.allow_trusted_contacts ? "Enabled" : "Disabled"}
        </p>

        <p>
          MyChart Integration:{" "}
          {settings?.allow_mychart_integration ? "Enabled" : "Disabled"}
        </p>

        <p>Reminders: {settings?.enable_reminders ? "Enabled" : "Disabled"}</p>
      </div>
    </aside>
  );
}
