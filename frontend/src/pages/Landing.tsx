import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import './Landing.css';

export function Landing() {
  const { user } = useAuth();

  return (
    <div className="landing">
      <nav className="landing__nav">
        <span className="landing__logo">SOCIETY TRACKER</span>
        <div className="landing__nav-links">
          {user ? (
            <Link to={user.role === 'admin' ? '/admin' : '/'} className="btn btn--primary btn--small">
              DASHBOARD
            </Link>
          ) : (
            <>
              <Link to="/login" className="btn btn--secondary btn--small">
                LOGIN
              </Link>
              <Link to="/register" className="btn btn--primary btn--small">
                REGISTER
              </Link>
            </>
          )}
        </div>
      </nav>

      <section className="landing__hero">
        <h1 className="landing__title">
          MANAGE
          <br />
          YOUR
          <br />
          SOCIETY
        </h1>
        <p className="landing__subtitle">
          Raise complaints. Track status. Stay informed.
        </p>
        <div className="landing__cta">
          {user ? (
            <Link to={user.role === 'admin' ? '/admin' : '/'} className="btn btn--primary btn--large">
              GO TO DASHBOARD
            </Link>
          ) : (
            <>
              <Link to="/register" className="btn btn--primary btn--large">
                GET STARTED
              </Link>
              <Link to="/login" className="btn btn--ghost btn--large">
                ALREADY HAVE AN ACCOUNT?
              </Link>
            </>
          )}
        </div>
      </section>

      <section className="landing__features">
        <div className="landing__feature">
          <div className="landing__feature-number">01</div>
          <h3 className="landing__feature-title">RAISE COMPLAINTS</h3>
          <p className="landing__feature-desc">
            Submit maintenance issues with category, description, and photo evidence.
            Track every complaint from submission to resolution.
          </p>
        </div>
        <div className="landing__feature">
          <div className="landing__feature-number">02</div>
          <h3 className="landing__feature-title">TRACK STATUS</h3>
          <p className="landing__feature-desc">
            Every status change is recorded with a timestamp and admin notes.
            Know exactly where your complaint stands at all times.
          </p>
        </div>
        <div className="landing__feature">
          <div className="landing__feature-number">03</div>
          <h3 className="landing__feature-title">NOTICE BOARD</h3>
          <p className="landing__feature-desc">
            Important society notices delivered to all residents.
            Email notifications for critical updates.
          </p>
        </div>
      </section>

      <section className="landing__roles">
        <div className="landing__role-card">
          <h3 className="landing__role-title">RESIDENT</h3>
          <ul className="landing__role-list">
            <li>Register and log in</li>
            <li>Submit complaints with photos</li>
            <li>View full status history</li>
            <li>Read society notices</li>
          </ul>
        </div>
        <div className="landing__role-card landing__role-card--admin">
          <h3 className="landing__role-title">ADMIN</h3>
          <ul className="landing__role-list">
            <li>Dashboard with live stats</li>
            <li>Filter and manage all complaints</li>
            <li>Update status and priority</li>
            <li>Post notices and manage users</li>
          </ul>
        </div>
      </section>

      <footer className="landing__footer">
        <span>BUILT WITH FASTAPI + REACT</span>
        <span>RAWBLOCK DESIGN SYSTEM</span>
      </footer>
    </div>
  );
}
