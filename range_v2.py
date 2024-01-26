import threading
import time
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import sessionmaker, relationship, scoped_session, declarative_base
from flask import Flask, request, jsonify
from rich import print
app = Flask(__name__)
Base = declarative_base()
# Attach to desired Database
range_engine = create_engine('mysql+pymysql://localhost/database')
SessionFactory = scoped_session(sessionmaker(bind=range_engine))
session = SessionFactory()


# Table for Site Locations
class Site(Base):
    __tablename__ = 'site'
    id = Column(Integer, primary_key=True)
    name = Column(String(7), unique=True)
    status = Column(String(4), default="down")
    status_history = relationship("StatusHistory", back_populates='site')
    ip_address = Column(String(15))
    mac_address = Column(String(17))
    is_tracked = Column(Boolean, default=True)

    def __repr__(self):
        return f'<Site(name={self.name},status={self.status}>'


# Table for Site Connectivity History
class StatusHistory(Base):
    __tablename__ = 'status_history' # noqa
    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("site.id"))
    status = Column(String(4), default="down")
    status_time = Column(DateTime, default=datetime.utcnow)
    duration = Column(Float)
    site = relationship('Site', back_populates="status_history")


# Create the tables in the database if they do not already exist
try:
    Base.metadata.create_all(bind=range_engine)
except Exception as e:
    print(e)


def start_flask():
    app.run(host='0.0.0.0', port=42069, debug=False)


# Creates the Flask API endpoint for remote sites to interact with
@app.route('/update-status/<site_name>', methods=["POST"])
def update_status(site_name):
    try:
        data = request.get_json()
        site = data.get('site')
        status = data.get('status')
        timer = data.get('timer')
        status = status.lower()
        api_status = session.query(Site).filter_by(name=site, is_tracked=True).first()
        if not site or not status:
            return jsonify({"Error": f"Site with name '{site}' not found"}), 404
        if api_status:
            api_status_history = StatusHistory(site_id=api_status.id,
                                               status=status,
                                               duration=abs(round((time.time() - float(timer))*1000, 2))
                                               )
            session.add(api_status_history)
            api_status.status = status
            session.commit()
            return jsonify({"message": f"{site} status updated to {status}"}), 200
        if not api_status:
            return jsonify({"Error": f"Site with name '{site}' not found in database."}), 404
        if status != "up":
            return jsonify({f"Error": "Invalid status, should be 'up'"}), 400

    except Exception as e:
        session.rollback()
        return jsonify({"Error": "Internal Error"}), 500
    finally:
        session.close()


# Report sites offline
# def offline_site():
#     done = False
#     timeit = round(time.time(), 0)
#     while 1:
#         if round(time.time(), 0) % 1 == 0 and not done:
#             try:
#                 timeit = round(time.time(), 0)
#                 for site in session.query(Site).filter(Site.is_tracked == True):
#                     check_status = session.query(StatusHistory).filter_by(site_id=site.id).first()
#                     if check_status is None:
#                         check_status = StatusHistory(site_id=site.id)
#                         session.add(check_status)
#                     elif check_status.status_time < datetime.utcnow() - timedelta(0, 1) and check_status.status != "up":
#                         check_status_updated = StatusHistory(site_id=site.id, status="down")
#                         session.add(check_status_updated)
#                         site.status = "down"
#                 session.commit()
#                 done = True
#             except Exception as e:
#                 session.rollback()
#                 print(e)
#         elif (timeit + 1) <= round(time.time(), 0):
#             done = False


# Adding additional sites to be tracked in the database
def manual_add_site():
    try:
        site_name = input("Enter Site Name:")
        ip_address = input("Enter IP Address:")
        mac_address = input("Enter MAC Address:")
        add_new_site = Site(name=site_name,
                        ip_address=ip_address,
                        mac_address=mac_address
                        )
        check_existing_site = session.query(Site).filter_by(name=site_name).first()
        if not check_existing_site:
            session.add(add_new_site)
            session.commit()
        else:
            print(f"[green]Site [cyan]{site_name}[/cyan] exists[/]\n")
    except Exception as e:
        session.rollback()
        print(e)
    finally:
        session.close()


# Deleting / disabling tracking on a particular site
def manual_del_site():
    try:
        site_name = input("Enter Site Name:")
        existing_site = session.query(Site).filter_by(name=site_name).first()
        if existing_site:
            existing_site.is_tracked = False
            session.commit()
            print(f"[orange]Site {site_name} is no longer being tracked.[/]\n")
        else:
            print(f"[orange]Site {site_name} does not exist.[/]\n")
    except Exception as err:
        print(err)
        session.close()
    finally:
        session.close()


# Manages the threading depending on user input
def input_thread():
    while True:
        user_input = input(f"\nPress 'a' to add a site, 'd' to remove site, and 'q' to quit: \n")
        if user_input.lower() == "a":
            manual_add_site()
        elif user_input.lower() == "d":
            manual_del_site()
        elif user_input.lower() == "q":
            break


if __name__ == "__main__":
    input_thread = threading.Thread(target=input_thread)
    flask_thread = threading.Thread(target=start_flask)
    # offline_thread = threading.Thread(target=offline_site)
    input_thread.start()
    flask_thread.start()
    # offline_thread.start()
    input_thread.join()
    flask_thread.join()
    # offline_thread.join()
